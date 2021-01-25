from django.db import models
from django.conf import settings

from api.models.utils import EngageManager
from api.models.configuration import Model, Scenario
from taskmeta.models import CeleryTask

import pandas as pd
import numpy as np
import os
import requests


class Run(models.Model):
    class Meta:
        db_table = "run"
        verbose_name_plural = "[5] Runs"
        ordering = ['year', '-created']
    objects = EngageManager()
    objects_all = models.Manager()

    scenario = models.ForeignKey(Scenario, on_delete=models.CASCADE)
    subset_time = models.CharField(max_length=200)
    year = models.IntegerField()
    status = models.CharField(max_length=200)
    message = models.TextField(blank=True)
    inputs_path = models.TextField(blank=True)
    logs_path = models.TextField(blank=True)
    outputs_path = models.TextField(blank=True)
    outputs_key = models.TextField(blank=True)
    plots_path = models.TextField(blank=True)
    model = models.ForeignKey(Model, on_delete=models.CASCADE)
    description = models.TextField(blank=True, null=True)
    deprecated = models.BooleanField(default=False)
    published = models.BooleanField(default=False, blank=True, null=True)
    created = models.DateTimeField(auto_now_add=True, null=True)
    updated = models.DateTimeField(auto_now=True, null=True)
    deleted = models.DateTimeField(default=None, editable=False, null=True)

    build_task = models.ForeignKey(
        to=CeleryTask,
        to_field="id",
        related_name="build_run",
        null=True,
        on_delete=models.PROTECT,
        default=None
    )

    run_task = models.ForeignKey(
        to=CeleryTask,
        to_field="id",
        related_name="model_run",
        null=True,
        on_delete=models.PROTECT,
        default=None
    )

    def __str__(self):
        return '%s (%s) @ %s' % (self.model, self.subset_time, self.updated)


class Cambium():

    @staticmethod
    def push_run(run):
        if not run.outputs_key:
            data = {
                'filename': run.outputs_key,
                'processor': 'engage',
                'project_name': run.model.name,
                'project_uuid': run.model.uuid,
                'project_source': 'Engage',
                'extras': {"scenario": run.scenario.name, "year": run.year},
                'private_key': settings.CAMBIUM_API_KEY
            }
            try:
                # Cambium Request
                url = 'https://cambium.nrel.gov/api/ingest_data/'
                response = requests.post(url, data=data)
                msg = response['message']

                # Handle Response
                if msg == "SUCCESS":
                    run.model.run_set.filter(
                        year=run.year,
                        scenario_id=run.scenario_id).update(published=False)
                    run.published = True
                elif msg in ["SUBMITTED", "RECEIVED", "STARTED", "PENDING"]:
                    run.published = None
                elif msg in ["FAILURE"]:
                    run.published = False
                run.save()
                return msg
            except Exception as e:
                return str(e)
        else:
            return 'Data has not been transferred to S3 bucket'


class Haven():

    def __init__(self, scenario):
        self.scenario = scenario
        self.model = scenario.model

        self.RUN = None
        self.YEARS = []
        self.TS_META = {}
        self.DATA = {}
        self.CAP_GEN_VALS = {}

    def get_data(self, aggregate, stations_only):
        # Stations
        df = pd.DataFrame(list(self.model.loc_techs.values(
            'id', 'technology__name',
            'technology__pretty_name',
            'technology__tag',
            'technology__pretty_tag',
            'location_1__name',
            'location_2__name')))
        df['technology__tag'] = df['technology__tag'].fillna('0')
        df['technology'] = df['technology__name'] + '-' + df['technology__tag']
        df.drop(['technology__tag', 'technology__name'], inplace=True, axis=1)
        df.columns = ['id', 'location_1', 'location_2',
                      'name', 'tag', 'technology']
        df.set_index('id', drop=False, inplace=True)
        self.stations = df
        self.DATA["stations"] = df.to_dict(orient='records')

        if stations_only is False:
            # Capacity / Generation
            runs = Run.objects.filter(
                scenario=self.scenario, deprecated=False).order_by('-updated')
            for run in runs:
                if run.outputs_path != "":
                    if run.year not in self.YEARS:
                        self.RUN = run
                        self._load_run()

            self.DATA["timeseries_meta"] = self.TS_META
            self.DATA["capacity_generation"] = self.CAP_GEN_VALS
        else:
            self.DATA["timeseries_meta"] = "stations_only must be false"
            self.DATA["capacity_generation"] = "stations_only must be false"

        # Optional: Aggregation
        if aggregate is None:
            return self.DATA
        else:
            return self._aggregate(aggregate, stations_only)

    @staticmethod
    def _get_loc_label(technology):
        try:
            return technology.split(':')[1]
        except Exception:
            return None

    @staticmethod
    def _get_tech_label(technology):
        return technology.split(':')[0]

    def _lookup_id(self, tech, loc):
        mask_l1 = self.stations.location_1 == loc
        loc_2 = self._get_loc_label(tech)
        if loc_2:
            mask_l2 = self.stations.location_2 == loc_2
        else:
            mask_l2 = self.stations.location_2.isnull()
        mask_t = self.stations.technology == self._get_tech_label(tech)
        ids = self.stations[mask_l1 & mask_l2 & mask_t]['id']
        try:
            return int(ids.values[0])
        except Exception:
            return "Not Found"

    def _aggregate(self, aggregate, stations_only):

        key = None  # Used for error logging in Exception
        year = None
        try:
            # Stations
            grouped = {}
            for key, ids in aggregate.items():
                group = self.stations.loc[ids].to_dict(orient='records')
                if key not in grouped:
                    grouped[key] = group
            self.DATA["stations"] = grouped

            if stations_only is True:
                return self.DATA

            # Capacity / Generation
            capacity_generation = self.DATA["capacity_generation"]
            aggregated = {}
            for year in capacity_generation:
                if year not in self.TS_META:
                    continue
                n_ts = len(self.TS_META[year])
                aggregated[year] = {}
                cap_gen_all = pd.DataFrame(capacity_generation[year])
                for key, ids in aggregate.items():
                    cap_gen = cap_gen_all[cap_gen_all['id'].isin(ids)]
                    group_cap = cap_gen.capacity.sum()
                    group_gen = np.array(cap_gen.generation.values.tolist())

                    if (len(group_gen) > 0):
                        group_gen = list(group_gen.sum(axis=0))
                    else:
                        group_gen = list(np.zeros(n_ts))
                    group_cap_gen = {
                        'ids': ids,
                        'capacity': group_cap,
                        'generation': group_gen
                    }
                    aggregated[year][key] = group_cap_gen
            self.DATA["capacity_generation"] = aggregated

            return self.DATA

        except Exception as e:
            dbg = ('e:', str(e), 'year:', year, 'key:', key)
            return "Aggregation failed: {}".format(dbg)

    def _load_run(self):
        self.YEARS.append(self.RUN.year)
        self.CAP_GEN_VALS[self.RUN.year] = []
        try:
            # load capacity data
            e_cap = self._load_csv('results_energy_cap.csv')
            # load generation data
            carrier_con = self._load_csv('results_carrier_con.csv')
            carrier_prod = self._load_csv('results_carrier_prod.csv')
            con_prod = pd.concat([carrier_con, carrier_prod],
                                 ignore_index=True)
            # Set timeseries
            ts = list(np.unique(con_prod[3].values))
            self.TS_META[self.RUN.year] = ts
            con_prod[3] = pd.to_datetime(con_prod[3])
            # build capacity and generation
            for _, row in e_cap.iterrows():
                loc_val = row[0]
                tech_val = row[1]
                cap_val = row[2]
                loc_mask = con_prod[0] == loc_val
                tech_mask = con_prod[1] == tech_val
                subset = con_prod[loc_mask & tech_mask]
                subset = subset.groupby(3).sum()
                gen_vals = list(subset[4].values)
                self.CAP_GEN_VALS[self.RUN.year].append({
                    'id': self._lookup_id(tech_val, loc_val),
                    'location_1': loc_val,
                    'location_2': self._get_loc_label(tech_val),
                    'technology': self._get_tech_label(tech_val),
                    'capacity': cap_val,
                    'generation': gen_vals})
        except Exception as e:
            self.CAP_GEN_VALS[self.RUN.year] = [str(e)]

    def _load_csv(self, fname, header=None):
        path = os.path.join(self.RUN.outputs_path, fname)
        return pd.read_csv(path, header=header)
