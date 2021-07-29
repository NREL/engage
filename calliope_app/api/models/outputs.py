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
import glob

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

    calliope_066_upgraded = models.BooleanField(default=False)
    calliope_066_errors = models.TextField(blank=True)

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
        meta['names'] = names.set_index('techs')['names'].to_dict()
        # Colors
        colors = self.read_output('inputs_colors.csv')
        meta['colors'] = colors.set_index('techs')['colors'].to_dict()
        # Locations
        locations = self.read_output('inputs_loc_coordinates.csv')
        meta['locations'] = sorted(locations['locs'].unique())
        # Remotes (Transmission Technologies)
        remotes = self.read_output('inputs_lookup_remotes.csv')
        remotes = remotes['techs'].unique()
        meta['remotes'] = list(remotes)
        meta['transmissions'] = list(set([t.split(':')[0] for t in remotes]))
        # Demands
        parents = self.read_output('inputs_inheritance.csv')
        parents = parents.groupby('inheritance')['techs'].apply(list)['demand']
        meta['demands'] = parents
        # Months
        meta['months'] = self.get_months()
        # Carriers
        c1 = self.read_output('inputs_lookup_loc_techs_conversion.csv')
        if c1 is not None:
            c1 = c1[['carrier_tiers', 'lookup_loc_techs_conversion']]
        else:
            c1 = pd.DataFrame(columns=['carrier_tiers',
                                       'lookup_loc_techs_conversion'])
        c2 = self.read_output('inputs_lookup_loc_techs_conversion_plus.csv')
        if c2 is not None:
            c2 = c2[['carrier_tiers', 'lookup_loc_techs_conversion_plus']]
        else:
            c2 = pd.DataFrame(columns=['carrier_tiers',
                                       'lookup_loc_techs_conversion_plus'])
        c1.columns = c2.columns = ['carrier_tiers', 'ltc']
        c = c1.append(c2)
        c['production'] = c['carrier_tiers'].str.contains('out')
        del c['carrier_tiers']
        c3 = self.read_output('inputs_lookup_loc_techs.csv')
        c3 = c3[['lookup_loc_techs']]
        c3.columns = ['ltc']
        c3['production'] = True
        c = c.append(c3)
        # Uncompress rows that have multiple Carriers (comma delimited)
        compress_mask = c['ltc'].str.contains(',')
        compressed_rows = c[compress_mask]
        c = c[~compress_mask]
        for i, row in compressed_rows.iterrows():
            for item in row['ltc'].split(','):
                c.append([row['production'], item])
        # Split into Location, Technology, Carrier
        c[['locs', 'techs', 'carrier']] = c['ltc'].str.split('::', expand=True)
        # Filter
        c.loc[c['techs'].isin(meta['demands']), 'production'] = False
        # Response
        meta['carriers_in'] = c[c['production'] == False].groupby(
            'carrier')['techs'].apply(lambda x: list(set(x))).to_dict()
        meta['carriers_out'] = c[c['production'] == True].groupby(
            'carrier')['techs'].apply(lambda x: list(set(x))).to_dict()
        # Get a list of all carriers (sorted by # technologies)
        carriers = {**meta['carriers_in'], **meta['carriers_out']}
        carriers = [(key, len(values)) for key, values in carriers.items()]
        carriers = sorted(carriers, key=lambda k: k[1], reverse=True)
        meta['carriers'] = [k[0] for k in carriers]
        return meta

    def get_viz_data(self, carrier, location, month):
        response = {}
        meta = self.get_meta()
        locations = []
        METRICS = ['Production', 'Consumption', 'Storage', 'Costs']
        if carrier not in meta['carriers']:
            carrier = meta['carriers'][0]
        if location not in meta['locations']:
            location = None
        if month not in meta['months']:
            month = meta['months'][0] if meta['months'] else None
        # Metrics
        for metric in METRICS:
            data = {}
            # Filters
            if metric == 'Consumption':
                hard_filter = meta['carriers_in'].get(carrier, [])
            else:
                hard_filter = meta['carriers_out'].get(carrier, [])
            soft_filter = \
                meta['carriers_in'].get(carrier, []) + \
                meta['carriers_out'].get(carrier, [])
            # Fixed Values (Barchart)
            data['barchart'], locs1 = self.get_static_values(
                meta, metric, location, soft_filter, hard_filter)
            # Variable Values (Timeseries)
            data['timeseries'], locs2 = self.get_variable_values(
                meta, carrier, metric, location, month, soft_filter)
            response[metric] = data
            locations += locs1 + locs2
        # Options
        response['options'] = {}
        response['options']['carrier'] = meta['carriers']
        response['options']['location'] = sorted(set(locations))
        response['options']['month'] = meta['months']
        return response

    def get_static_values(self, meta, metric, location,
                          soft_filter, hard_filter):
        LABELS = {'Production': 'Capacities',
                  'Consumption': 'Capacities',
                  'Storage': 'Storage Capacities',
                  'Costs': 'Fixed Costs'}
        if metric == 'Storage':
            # Storage Capacity
            df = self.read_output('results_storage_cap.csv')
            if df is None:
                df = pd.DataFrame(columns=['locs', 'techs', 'values'])
            else:
                df['values'] = df['storage_cap']
            ctx = self.read_output('inputs_storage_cap_max.csv')
            if ctx is not None:
                ctx['values'] = ctx['storage_cap_max']
        elif metric == 'Costs':
            # Investment Costs
            df = self.read_output('results_cost.csv')
            df['values'] = df['cost']
            ctx = None
        else:
            # Energy Capacity
            df = self.read_output('results_energy_cap.csv')
            df['values'] = df['energy_cap']
            ctx = self.read_output('inputs_energy_cap_max.csv')
            if ctx is not None:
                ctx['values'] = ctx['energy_cap_max']
        # Process Values
        df = df[~df['techs'].isin(meta['remotes'])]
        df = df[~df['techs'].isin(meta['demands'])]
        df = df[df['techs'].isin(soft_filter)]
        df = df[df['techs'].isin(hard_filter)]
        locations = list(df['locs'].unique())
        if location:
            df = df[df['locs'] == location]
        df = df.groupby('techs').sum()
        df = df['values'].to_dict()
        # Process Max Bounds Context (ctx)
        if ctx is not None:
            ctx = ctx.replace(np.inf, np.nan).dropna()
            if location:
                ctx = ctx[ctx['locs'] == location]
            ctx = ctx.groupby('techs').sum()
            ctx = ctx['values'].to_dict()
        else:
            ctx = {}
        # Viz Layers
        layers = [{'key': key,
                   'name': meta['names'][key] if key in meta['names'] else key,
                   'color': meta['colors'][key] if key in meta['colors'] else None,
                   'y': [value]} for key, value in df.items() if value != 0]
        layers = sorted(layers, key=lambda k: k['y'][0])
        layers_ctx = [{'name': d['name'],
                       'color': d['color'],
                       'y': [ctx.get(d['key'], d['y'][0])]} for d in layers]
        return {
            'base': {'x': [LABELS[metric]]},
            'layers': layers,
            'layers_ctx': layers_ctx,
        }, locations

    def get_variable_values(self, meta, carrier, metric,
                            location, month, soft_filter):
        ext = '_' + str(month) + '.csv' if month else '.csv'
        if metric == 'Storage':
            # Storage
            df = self.read_output('results_storage' + ext)
            if df is None:
                df = pd.DataFrame(
                    columns=['locs', 'techs', 'timesteps', 'values'])
            else:
                df['values'] = df['storage']
        elif metric == 'Costs':
            # Costs
            df = self.read_output('results_cost_var' + ext)
            df['values'] = df['cost_var']
        else:
            # Production / Consumption
            df = self.read_output('results_carrier_con' + ext)
            df['values'] = df['carrier_con']
            if metric == "Production":
                df2 = self.read_output('results_carrier_prod' + ext)
                df2['values'] = df2['carrier_prod']
                df = df.append(df2)
            else:
                df2 = self.read_output('results_carrier_export' + ext)
                if df2 is not None:
                    df2['values'] = -df2['carrier_export']
                    df = df.append(df2)
            # Unmet Demand
            df3 = self.read_output('results_unmet_demand' + ext)
            if df3 is not None:
                df3['values'] = df3['unmet_demand']
                df3['techs'] = 'Unmet Demand'
                df = df.append(df3)
                soft_filter.append('Unmet Demand')
                meta['colors']['Unmet Demand'] = "#FF000055"
            df = df[df['carriers'] == carrier]
        # Filter
        df = df[df['techs'].isin(soft_filter)]
        df['techs'] = df['techs'].str.split(':').str[0]
        locations = list(df['locs'].unique())
        if location:
            df = df[df['locs'] == location]
        else:
            df = df[~df['techs'].isin(meta['transmissions'])]
        # Process
        df = df.groupby(['techs', 'timesteps']).sum()
        pvalues, nvalues, techs, ts = [], [], [], []
        if 'values' in df.columns:
            df = df['values'].reset_index()
            ts = list(df['timesteps'].unique())
            for tech in df['techs'].unique():
                mask = df['techs'] == tech
                values_1 = df[mask]['values'].values
                # Split up Positive / Negative for Production / Consumption
                if metric == "Consumption":
                    is_primary = values_1 <= 0
                else:
                    is_primary = values_1 >= 0
                # Secondary
                if any(~is_primary):
                    values_2 = np.copy(values_1)
                    values_1[~is_primary] = 0
                    values_2[is_primary] = 0
                    if (np.sum(values_2) != 0) & (tech in meta['demands']):
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
        layers = sorted(
            layers,
            key=lambda k: (k['name'] == 'Unmet Demand',
                           -np.min(np.abs(k['y'])) / np.max(np.abs(k['y'])),
                           np.max(np.abs(k['y']))))
        data = {
            'base': {'x': ts},
            'layers': layers
        }
        if (metric == 'Production') & (len(nvalues) > 0):
            data['overlay'] = {'name': "Demand",
                               'y': list(np.sum(np.array(nvalues), axis=0))}
        return data, locations

    def read_output(self, file):
        fpath = os.path.join(self.outputs_path, file)
        try:
            return pd.read_csv(fpath, header=0)
        except FileNotFoundError:
            return None

    def get_months(self):
        fpath = os.path.join(self.outputs_path, 'results_carrier_prod_*.csv')
        months = sorted([m[-6:-4] for m in glob.glob(fpath)])
        return months


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
