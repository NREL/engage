import json
import logging
from urllib.parse import urljoin

from django.db import models
from django.conf import settings

from api.models.utils import EngageManager
from api.models.configuration import Model, Scenario
from taskmeta.models import CeleryTask

import pandas as pd
import numpy as np
import os
import requests

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


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

    def get_meta(self):
        meta = {}
        # Names
        names = self.read_output('inputs_names.csv')
        meta['names'] = names.set_index(0)[1].to_dict()
        # Colors
        colors = self.read_output('inputs_colors.csv')
        meta['colors'] = colors.set_index(0)[1].to_dict()
        # Locations
        locations = self.read_output('inputs_loc_coordinates.csv')
        meta['locations'] = list(locations[1].unique())
        # Remotes (Transmission Technologies)
        remotes = self.read_output('inputs_lookup_remotes.csv')
        meta['remotes'] = remotes[1].unique()
        # Demands
        parents = self.read_output('inputs_inheritance.csv')
        meta['demands'] = parents.groupby(1)[0].apply(list)['demand']
        # Carriers
        c1 = self.read_output('inputs_lookup_loc_techs_conversion.csv', [2, 3])
        c2 = self.read_output('inputs_lookup_loc_techs_conversion_plus.csv', [2, 3])
        c = c1.append(c2)
        c[2] = c[2].str.contains('out')
        c3 = self.read_output('inputs_lookup_loc_techs.csv', [1, 2])
        c3[1] = True
        c3.columns = [2, 3]
        c = c.append(c3)
        # Uncompress rows that have multiple Carriers (comma delimited)
        compress_mask = c[3].str.contains(',')
        compressed_rows = c[compress_mask]
        c = c[~compress_mask]
        for i, row in compressed_rows.iterrows():
            for item in row[3].split(','):
                c.append([row[2], item])
        # Split into Location, Technology, Carrier
        c[[4, 5, 6]] = c[3].str.split('::', expand=True)
        # Filter
        c = c[~c[5].isin(meta['remotes'])]
        c.loc[c[5].isin(meta['demands']), 2] = False
        # Response
        meta['carriers'] = list(c[6].unique())
        meta['carriers_in'] = c[c[2] == False].groupby(6)[5].apply(
            lambda x: list(set(x))).to_dict()
        meta['carriers_out'] = c[c[2] == True].groupby(6)[5].apply(
            lambda x: list(set(x))).to_dict()
        return meta

    def get_viz_data(self, carrier, metric, location):
        response = {}
        meta = self.get_meta()
        METRICS = ['Production', 'Consumption', 'Storage', 'Costs']
        unmet = self.read_output('results_unmet_demand.csv', [0])
        if not unmet.empty:
            METRICS += ['Unmet Demand']
        if carrier not in meta['carriers']:
            carrier = meta['carriers'][0]
        if metric not in METRICS:
            metric = METRICS[0]
        if location not in meta['locations']:
            location = None
        # Filters
        if metric == 'Consumption':
            hard_filter = meta['carriers_in'].get(carrier, [])
        else:
            hard_filter = meta['carriers_out'].get(carrier, [])
        soft_filter = \
            meta['carriers_in'].get(carrier, []) + \
            meta['carriers_out'].get(carrier, [])
        # Options
        response['options'] = {}
        response['options']['metric'] = METRICS
        response['options']['carrier'] = meta['carriers']
        response['options']['location'] = meta['locations']
        # Fixed Values (Barchart)
        if metric != 'Unmet Demand':
            response['barchart'] = self.get_static_values(
                meta, metric, location, soft_filter, hard_filter)
        # Variable Values (Timeseries)
        response['timeseries'] = self.get_variable_values(
            meta, carrier, metric, location, soft_filter)
        return response

    def get_static_values(self, meta, metric, location,
                          soft_filter, hard_filter):
        LABELS = {'Production': 'Capacity',
                  'Consumption': 'Capacity',
                  'Storage': 'Storage Capacity',
                  'Costs': 'Investment Cost'}
        if metric == 'Storage':
            # Storage Capacity
            df = self.read_output('results_storage_cap.csv', [0, 1, 2])
        elif metric == 'Costs':
            # Investment Costs
            df = self.read_output('results_cost_investment.csv', [0, 1, 3])
        else:
            # Energy Capacity
            df = self.read_output('results_energy_cap.csv', [0, 1, 2])
        df.columns = ['Location', 'Technology', 'Values']
        # Filter
        df = df[~df['Technology'].isin(meta['remotes'])]
        df = df[~df['Technology'].isin(meta['demands'])]
        df = df[df['Technology'].isin(soft_filter)]
        df = df[df['Technology'].isin(hard_filter)]
        if location:
            df = df[df['Location'] == location]
        # Process
        if metric == "Consumption":
            df['Values'] *= -1
        df = df.groupby('Technology').sum()
        df = df['Values'].to_dict()
        layers = [{'name': meta['names'][key] if key in meta['names'] else key,
                   'color': meta['colors'][key] if key in meta['colors'] else None,
                   'y': [value]} for key, value in df.items()]
        return {
            'base': {'x': [LABELS[metric]]},
            'layers': layers,
        }

    def get_variable_values(self, meta, carrier, metric,
                            location, soft_filter):
        if metric == 'Storage':
            # Storage
            df = self.read_output('results_storage.csv', [0, 1, 2, 3])
            df.columns = ['Location', 'Technology', 'Timestamp', 'Values']
        elif metric == 'Costs':
            # Costs
            df = self.read_output('results_cost_var.csv', [0, 1, 3, 4])
            df.columns = ['Location', 'Technology', 'Timestamp', 'Values']
        elif metric == 'Unmet Demand':
            # Unmet Demand
            df = self.read_output('results_unmet_demand.csv', [0, 1, 2, 3])
            df.columns = ['Location', 'Carrier', 'Timestamp', 'Values']
            df = df[df['Carrier'] == carrier]
            df['Technology'] = 'All Technologies'
        else:
            # Production / Consumption
            df = self.read_output('results_carrier_con.csv')
            if metric == "Production":
                df2 = self.read_output('results_carrier_prod.csv')
                df = df.append(df2)
            else:
                df2 = self.read_output('results_carrier_export.csv')
                df2[4] *= -1
                if not df2.empty:
                    df = df.append(df2)
            df.columns = ['Location', 'Technology', 'Carrier',
                          'Timestamp', 'Values']
            df = df[df['Carrier'] == carrier]
        # Filter
        if metric != 'Unmet Demand':
            df = df[~df['Technology'].isin(meta['remotes'])]
            df = df[df['Technology'].isin(soft_filter)]
            if location:
                df = df[df['Location'] == location]
        # Process
        df = df.groupby(['Technology', 'Timestamp']).sum()
        pvalues, nvalues, techs, ts = [], [], [], []
        if 'Values' in df.columns:
            df = df['Values'].reset_index()
            ts = list(df['Timestamp'].unique())
            for tech in df['Technology'].unique():
                mask = df['Technology'] == tech
                values_1 = df[mask]['Values'].values
                # Handle Unmet Demand (Does not vary by Technology)
                if metric == "Unmet Demand":
                    pvalues.append(list(values_1))
                    techs.append(tech)
                    continue
                # Split up Positive / Negative for Production / Consumption
                elif metric == "Consumption":
                    is_primary = values_1 <= 0
                else:
                    is_primary = values_1 >= 0
                # Secondary
                if any(~is_primary):
                    values_2 = np.copy(values_1)
                    values_1[~is_primary] = 0
                    values_2[is_primary] = 0
                    if np.sum(values_2) != 0:
                        nvalues.append(list(-values_2))
                # Primary
                if np.sum(values_1) != 0:
                    pvalues.append(list(values_1))
                    techs.append(tech)
        layers = [
            {'name': meta['names'][techs[i]] if techs[i] in meta['names'] else techs[i],
             'color': meta['colors'][techs[i]] if techs[i] in meta['colors'] else None,
             'group': 'Primary',
             'y': pvalues[i]
             } for i in range(len((techs)))]
        data = {
            'base': {'x': ts},
            'layers': layers
        }
        if (metric == 'Production') & (len(nvalues) > 0):
            data['overlay'] = {'name': "Demand",
                               'y': list(np.sum(np.array(nvalues), axis=0))}
        return data

    def read_output(self, file, columns=[]):
        fpath = os.path.join(self.outputs_path, file)
        try:
            if columns:
                df = pd.read_csv(fpath, header=None, usecols=columns)
            else:
                df = pd.read_csv(fpath, header=None)
        except FileNotFoundError:
            df = pd.DataFrame(columns=columns)
        return df


class Cambium():

    @staticmethod
    def push_run(run):
        if not run.outputs_key:
            return 'Data has not been transferred to S3 bucket'

        logger.info("Push run starts...")
        data = {
            'filename': run.outputs_key,
            'processor': 'engage',
            'project_name': run.model.name,
            'project_uuid': str(run.model.uuid),
            'project_source': 'Engage',
            'extras': json.dumps({"scenario": run.scenario.name, "year": run.year}),
            'private_key': settings.CAMBIUM_API_KEY,
            'asynchronous': True
        }
        logger.info("Call Cambium API to ingest data - %s", data["filename"])
        try:
            url = urljoin(settings.CAMBIUM_URL, "api/ingest-data/")
            response = requests.post(url, data=data).json()
            logger.info("Cambium API response: %s", json.dumps(response))
            if 'message' not in response:
                return "Invalid Request"

            # Handle Response
            msg = response["message"]
            status = response["status"]
            if status == "SUCCESS":
                run.model.run_set.filter(
                    year=run.year,
                    scenario_id=run.scenario_id).update(published=False)
                run.published = True
            elif status in ["SUBMITTED", "RECEIVED", "STARTED", "PENDING"]:
                run.published = None
            elif status in ["FAILURE", "FAILED"]:
                run.published = False
            run.save()
            return msg
        except Exception as e:
            logger.exception("Push run failed!")
            return str(e)
        logger.info("Push run success.")


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
