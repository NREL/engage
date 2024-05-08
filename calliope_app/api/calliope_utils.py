"""
This module contains support functions and libraries used in
interfacing with Calliope.
"""

import os
import yaml
import shutil
from calliope import Model as CalliopeModel
import pandas as pd
import json
import copy
import calendar

from api.models.configuration import Scenario_Param, Scenario_Loc_Tech, \
    Location, Tech_Param, Loc_Tech_Param, Loc_Tech, Scenario, Carrier
from api.models.outputs import Run
import logging


logger = logging.getLogger(__name__)


def get_model_yaml_set(run, scenario_id, year):
    """ Function pulls model parameters from Database for YAML """
    params = Scenario_Param.objects.filter(scenario_id=scenario_id,
                                           year__lte=year).order_by('-year')
    # Initialize the Return list
    model_yaml_set = {}
    # Tracks which parameters have already been set (prioritized by year)
    unique_params = []
    # Loop over Parameters
    for param in params:
        unique_param = param.run_parameter.root+'.'+param.run_parameter.name

        # NOTE: deprecated run parameter in the database
        if unique_param == "run.objective_options":
            continue
        
        if unique_param not in unique_params:
            # If parameter hasn't been set, add to Return List
            unique_params.append(unique_param)
            key_list = unique_param.split('.')
            dictify(model_yaml_set,key_list,param.value)
    dictify(model_yaml_set,['import'],'["techs.yaml","locations.yaml"]')
    logger.info(f"Run information: {run.id}, {run}")
    for param in run.run_options:
        logger.info(param)
        unique_param = param["root"] + '.' + param["name"]
        key_list = unique_param.split('.')
        dictify(model_yaml_set,key_list,param["value"])

    return model_yaml_set


def get_location_meta_yaml_set(scenario_id, existing = None):
    """ Function pulls model locations from Database for YAML """
    loc_techs = Scenario_Loc_Tech.objects.filter(scenario_id=scenario_id)
    loc_ids = loc_techs.values_list('loc_tech__location_1',
                                    'loc_tech__location_2')
    loc_ids = list(filter(None, set(
        [item for sublist in loc_ids for item in sublist])))
    locations = Location.objects.filter(id__in=loc_ids)
    # Initialize the Return dict
    if existing:
        location_coord_yaml_set = existing
    else:
        location_coord_yaml_set = {}
    # There are no timeseries in Location Coordinates
    is_timeseries = False
    # Loop over Parameters
    for loc in locations:
        # Coordinates
        coordinates = '{{"lat": {}, "lon": {}}}'.format(loc.latitude,
                                                        loc.longitude)
        param_list = ['locations', loc.name, 'coordinates']
        dictify(location_coord_yaml_set,param_list,coordinates)
        # Available Area
        if loc.available_area is None:
            continue
        param_list = ['locations', loc.name,
                      'available_area']
        dictify(location_coord_yaml_set,param_list,loc.available_area)
    return location_coord_yaml_set


def get_techs_yaml_set(scenario_id, year):
    """ Function pulls tech parameters from Database for YAML """
    loc_techs = Scenario_Loc_Tech.objects.filter(scenario_id=scenario_id)
    tech_ids = list(loc_techs.values_list('loc_tech__technology',
                                          flat=True).distinct())
    parameters = Tech_Param.objects.filter(technology_id__in=tech_ids,
                                           year__lte=year).order_by('-year')
    # Initialize the Return list
    techs_yaml_set = {}
    # Loop over Technologies
    for tech_id in tech_ids:
        params = parameters.filter(technology_id=tech_id)
        # Tracks which parameters have already been set (prioritized by year)
        unique_params = []
        # Loop over Parameters
        for param in params:
            unique_param = param.parameter.root+'.'+param.parameter.name
            if unique_param not in unique_params:
                # If parameter hasn't been set, add to Return List
                unique_params.append(unique_param)
                if param.timeseries:
                    value = "file={}--{}.csv:value".format(
                                    param.technology.calliope_name, unique_param.replace('.','-'))
                elif '%' in param.parameter.units:  # Calliope in decimal format
                    value = float(param.value) / 100
                else:
                    value = param.value
                param_list = ['techs', param.technology.calliope_name]+\
                              unique_param.split('.')
                dictify(techs_yaml_set,param_list,value)
    return techs_yaml_set


def get_loc_techs_yaml_set(scenario_id, year):
    """ Function pulls location technology (nodes)
    parameters from Database for YAML """
    loc_techs = Scenario_Loc_Tech.objects.filter(scenario_id=scenario_id)
    loc_tech_ids = list(loc_techs.values_list('loc_tech_id',
                                              flat=True).distinct())
    parameters = Loc_Tech_Param.objects.filter(
        loc_tech_id__in=loc_tech_ids, year__lte=year).order_by('-year')
    # Initialize the Return list
    loc_techs_yaml_set = {}
    # Loop over Technologies
    for loc_tech_id in loc_tech_ids:
        loc_tech = Loc_Tech.objects.get(id=loc_tech_id)
        params = parameters.filter(loc_tech=loc_tech)
        parent = loc_tech.technology.abstract_tech.name

        if parent == 'transmission':
            parent_type = 'links'
            location = \
                loc_tech.location_1.name + ',' + \
                loc_tech.location_2.name
        else:
            parent_type = 'locations'
            location = loc_tech.location_1.name
        technology = loc_tech.technology.calliope_name

        if len(params) == 0:
            param_list = [parent_type, location, 'techs',
                          technology]
            dictify(loc_techs_yaml_set,param_list,'')
            continue

        # Tracks which parameters have already been set (prioritized by year)
        unique_params = []
        # Loop over Parameters
        for param in params:
            unique_param = param.parameter.root+'.'+param.parameter.name
            if unique_param not in unique_params:
                # If parameter hasn't been set, add to Return List
                unique_params.append(unique_param)
                if param.timeseries:
                    value = "file={}--{}--{}.csv:value".format(
                                    location, technology, unique_param.replace('.','-'))
                elif '%' in param.parameter.units:  # Calliope in decimal format
                    value = float(param.value) / 100
                else:
                    value = param.value
                    
                param_list = [parent_type, location, 'techs',
                              param.loc_tech.technology.calliope_name]+\
                              unique_param.split('.')
                dictify(loc_techs_yaml_set,param_list,value)
    return loc_techs_yaml_set

def get_carriers_yaml_set(scenario_id):
    model = Scenario.objects.get(id=scenario_id).model
    
    carriers_yaml_set = {}
    for carrier in model.carriers.all():
        carriers_yaml_set[carrier.name] = {'rate':carrier.rate_unit,'quantity':carrier.quantity_unit}
    for carrier in model.carriers_old:
        if carrier not in carriers_yaml_set:
            carriers_yaml_set[carrier] = {'rate':'kW','quantity':'kWh'}

    return carriers_yaml_set

# This function takes a target dict and adds a new entry from an array of nested dict keys
# The final value in the array is the entry value and the rest of the list is the nested keys
# Creates any missing keys in the nested list
def dictify(target, keys, value):
    # Build the nested dict structure (if neccessary) by adding any
    # nested keys in the list before the final key/value pair
    # Strip out/skip any entries with an empty key
    keys = [k for k in keys if k != '']
    if len(keys) > 1:
        for key in keys[:-1]:
            if key not in target.keys():
                target[key] = {}
            target = target[key]

    # Handle blank, T/F, float, and JSON string values
    # As of Calliope 0.6.8 all "False" values should be set to none/null
    if value == "":
            target[keys[-1]] = None
    elif value == 'True':
            target[keys[-1]] = True
    elif value == 'False':
            target[keys[-1]] = False
    else:
        # Try converting string to JSON object or float before saving as flat string
        try:
            string = value.replace(", ", ",")
            for char in ['\'', '“', '”', '‘', '’']:
                string = string.replace(char, '\"')
            target[keys[-1]] = json.loads(string)
        except Exception:
            try:
                target[keys[-1]] = float(value)
            except ValueError:
                target[keys[-1]] = value

def stringify(param_list):
    param_list = [str(x) for x in param_list]
    return '||'.join(param_list).replace('||||', '||')


def run_basic(model_path, logger):
    """ Basic Run """
    logger.info('--- Run Basic')
    model = CalliopeModel(config=model_path)
    logger.info(model.info())
    logger.info(model._model_data.coords.get("techs_non_transmission", []))
    model.run()
    _write_outputs(model, model_path)
    return model.results.termination_condition


def run_clustered(model_path, idx, logger):
    """ Clustered Capacity Expansion w/ Monthly Operational Runs """
    logger.info('--- Run Clustering')
    _set_clustering(model_path, on=True)
    _set_subset_time(model_path)
    _set_capacities(model_path)
    model = CalliopeModel(config=model_path)
    model.run()
    _write_outputs(model, model_path)
    if model.results.termination_condition != 'optimal':
        return model.results.termination_condition
    # Results
    capacity, storage, units, demand_techs = _get_cap_results(model)
    # Monthly Dispatch
    year = idx.year[0]
    months = list(idx.month.unique())
    for month in months:
        try:
            logger.info('--- Run Operational Month: {}'.format(month))
            days = idx[idx.month == month]
            st = '{}-{}-{} 00:00'.format(year, _pad(month), _pad(days.min().day))
            et = '{}-{}-{} 23:00'.format(year, _pad(month), _pad(days.max().day))
            _set_clustering(model_path, on=False)
            _set_subset_time(model_path, st, et)
            _set_capacities(model_path, demand_techs, capacity, storage, units)
            model = CalliopeModel(config=model_path)
            model.run()
            _write_outputs(model, model_path, _pad(month))
        except Exception as e:
            logger.error(e)
            pass
    _reset_configs(model_path)
    return 'optimal'


def _set_clustering(model_path, on=False, k=14):
    # Read
    with open(model_path) as file:
        model_yaml = yaml.load(file, Loader=yaml.FullLoader)
    # Update
    if on is True:
        time = {}
        time['function'] = "apply_clustering"
        time['function_options'] = {}
        time['function_options']['clustering_func'] = "kmeans"
        time['function_options']['how'] = "mean"
        time['function_options']['k'] = k
    else:
        time = None
    model_yaml['model']['time'] = time
    # Write
    with open(model_path, 'w') as file:
        yaml.dump(model_yaml, file)


def _set_subset_time(model_path, start_time=None, end_time=None):
    # Read
    with open(model_path) as file:
        model_yaml = yaml.load(file, Loader=yaml.FullLoader)
    # Update
    if start_time is not None:
        subset_time = [start_time, end_time]
    else:
        subset_time = None
    model_yaml['model']['subset_time'] = subset_time
    # Write
    with open(model_path, 'w') as file:
        yaml.dump(model_yaml, file)


def _set_capacities(model_path, ignore_techs=[],
                    capacity=None, storage=None, units=None):
    # ---- UPDATE MODEL REFERENCE
    # Read
    with open(model_path) as file:
        model_yaml = yaml.load(file, Loader=yaml.FullLoader)
    # Update Model Settings
    if capacity is None:
        model_yaml['import'] = ['techs.yaml', 'locations.yaml']
    else:
        model_yaml['import'] = ['techs.yaml', 'locations_fixed.yaml']
    # Write
    with open(model_path, 'w') as file:
        yaml.dump(model_yaml, file)
    if capacity is None:
        return
    # ---- UPDATE CAPACITIES
    # Read
    locations_path = model_path.replace('model.yaml', 'locations.yaml')
    with open(locations_path) as file:
        locations_yaml = yaml.load(file, Loader=yaml.FullLoader)
    # Update Locations Settings
    for loc, loc_data in locations_yaml['locations'].items():
        if 'techs' not in loc_data:
            continue
        for tech, tech_data in loc_data['techs'].items():
            if tech in ignore_techs:
                continue
            key = loc + '::' + tech
            if not tech_data:
                tech_data = {}
            if 'constraints' not in tech_data.keys():
                tech_data['constraints'] = {}
            if key in units:
                tech_data['constraints']['units_equals'] = int(units[key])
            elif key in capacity:
                tech_data['constraints']['energy_cap_equals'] = float(capacity[key])
            if key in storage:
                tech_data['constraints']['storage_cap_equals'] = float(storage[key])
            locations_yaml['locations'][loc]['techs'][tech] = tech_data
    # Update Links Settings
    for loc, loc_data in locations_yaml['links'].items():
        if 'techs' not in loc_data:
            continue
        for tech, tech_data in loc_data['techs'].items():
            locs = loc.split(',')
            key = locs[0] + '::' + tech + ':' + locs[1]
            if not tech_data:
                tech_data = {}
            if 'constraints' not in tech_data.keys():
                tech_data['constraints'] = {}
            if key in capacity:
                tech_data['constraints']['energy_cap_equals'] = \
                    float(capacity[key])
            locations_yaml['links'][loc]['techs'][tech] = tech_data
    # Write
    locations_path = locations_path.replace('locations.yaml',
                                            'locations_fixed.yaml')
    with open(locations_path, 'w') as file:
        yaml.dump(locations_yaml, file)


def _get_cap_results(model):
    # Capacities
    _cap_techs = model.results.energy_cap.loc_techs.values
    _cap_vals = model.results.energy_cap.values
    capacity = dict(zip(_cap_techs, _cap_vals))
    # Storage Capacities
    try:
        _storage_techs = model.results.storage_cap.loc_techs_store.values
        _storage_vals = model.results.storage_cap.values
        storage = dict(zip(_storage_techs, _storage_vals))
    except AttributeError:
        storage = {}
    # Installed Units
    try:
        _unit_techs = model.results.units.loc_techs_milp.values
        _unit_vals = model.results.units.values.astype(int)
        units = dict(zip(_unit_techs, _unit_vals.astype(int)))
    except AttributeError:
        units = {}
    # Demand Techs
    _demands = [t == 'demand' for t in model.inputs.inheritance.values]
    demand_techs = list(model.inputs.inheritance.techs.values[_demands])
    return capacity, storage, units, demand_techs


def _pad(number):
    number = int(number)
    return str(number) if number >= 10 else '0' + str(number)


def _reset_configs(model_path):
    _set_clustering(model_path)
    _set_subset_time(model_path)
    _set_capacities(model_path)


def _write_outputs(model, model_path, ts_only_suffix=None):
    TS_FILES = ['results_capacity_factor.csv',
                'results_carrier_con.csv',
                'results_carrier_prod.csv',
                'results_cost_var.csv',
                'results_resource_con.csv',
                'results_storage.csv',
                'results_unmet_demand.csv']
    base_path = os.path.dirname(os.path.dirname(model_path))
    folder = "outputs_tmp" if ts_only_suffix else "outputs"
    folder = os.path.join(base_path, folder)
    if not os.path.exists(folder):
        os.makedirs(folder, exist_ok=True)
    save_outputs = os.path.join(base_path, folder, "model_outputs")
    if os.path.exists(save_outputs):
        shutil.rmtree(save_outputs)
    model.to_csv(save_outputs)
    final_outputs = None
    if ts_only_suffix is not None:
        final_outputs = os.path.join(base_path, "outputs/model_outputs")
        for file in TS_FILES:
            try:
                with open(os.path.join(save_outputs, file), 'r') as i:
                    f = file.replace('.csv', '_{}.csv'.format(ts_only_suffix))
                    with open(os.path.join(final_outputs, f), 'w') as o:
                        o.write(i.read())
            except Exception:
                pass
        shutil.rmtree(os.path.join(base_path, folder))
    if final_outputs:
        _yaml_outputs(model_path,final_outputs)
    else:
        _yaml_outputs(model_path,save_outputs)

def _yaml_outputs(model_path, outputs_dir):
    base_path = os.path.dirname(os.path.dirname(model_path))
    results_var = {'energy_cap':'results_energy_cap.csv','storage_cap':'results_storage_cap.csv'}
    inputs_dir = os.path.join(base_path, 'inputs')

    model = yaml.load(open(os.path.join(inputs_dir,'model.yaml')), Loader=yaml.FullLoader)
    model.update(yaml.load(open(os.path.join(inputs_dir,'locations.yaml')), Loader=yaml.FullLoader))
    model.update(yaml.load(open(os.path.join(inputs_dir,'techs.yaml')), Loader=yaml.FullLoader))

    has_outputs = False
    for v in results_var.keys():
        if not os.path.exists(os.path.join(outputs_dir,results_var[v])):
            continue
        has_outputs = True
        r_df = pd.read_csv(os.path.join(outputs_dir,results_var[v]))

        for tl in ['locations','links']:
            for l in model[tl].keys():
                if tl == 'links':
                    l1 = l.split(',')[0]
                    l2 = l.split(',')[1]
                if 'techs' in model[tl][l].keys():
                    for t in model[tl][l]['techs'].keys():
                        if v == 'storage_cap' and model['techs'][t]['essentials']['parent'] not in ['storage','supply_plus']:
                            continue

                        if model[tl][l]['techs'][t] is None:
                            model[tl][l]['techs'][t] = {}
                        if 'results' not in model[tl][l]['techs'][t]:
                            model[tl][l]['techs'][t]['results'] = {}
                        if tl == 'links':
                            if r_df.loc[(r_df['locs'] == l1) & (r_df['techs'] == t+':'+l2)].empty:
                                model[tl][l]['techs'][t]['results'][v+'_equals'] = 0
                            else:
                                model[tl][l]['techs'][t]['results'][v+'_equals'] = float(r_df.loc[(r_df['locs'] == l1) &
                                                                                (r_df['techs'] == t+':'+l2)][v].values[0])
                        else:
                            if r_df.loc[(r_df['locs'] == l) & (r_df['techs'] == t)].empty:
                                model[tl][l]['techs'][t]['results'][v+'_equals'] = 0
                            else:
                                model[tl][l]['techs'][t]['results'][v+'_equals'] = float(r_df.loc[(r_df['locs'] == l) &
                                                                                    (r_df['techs'] == t)][v].values[0])
    if has_outputs:
        yaml.dump(model, open(os.path.join(outputs_dir,'model_results.yaml'),'w+'), default_flow_style=False)

def apply_gradient(old_inputs,old_results,new_inputs,old_year,new_year,logger):
    old_model = yaml.safe_load(open(old_results+'/model_results.yaml'))

    new_techs = yaml.safe_load(open(new_inputs+'/techs.yaml','r'))
    new_loctechs = yaml.safe_load(open(new_inputs+'/locations.yaml','r'))
    new_model = yaml.safe_load(open(new_inputs+'/model.yaml','r'))

    built_tech_names = []
    built_techs = {}
    built_loc_techs = {}

    for l in old_model['locations']:
        if 'techs' in old_model['locations'][l]:
            for t in old_model['locations'][l]['techs']:
                old_tech = old_model['techs'][t]
                new_tech = new_techs['techs'][t]
                new_loc_tech = new_loctechs['locations'][l]['techs'][t]
                loc_tech = old_model['locations'][l]['techs'][t]
                if ('energy_cap_max' in loc_tech.get('constraints',{}) or 'storage_cap_max' in loc_tech.get('constraints',{})) or\
                        ('energy_cap_max' in old_tech.get('constraints',{}) or 'storage_cap_max' in old_tech.get('constraints',{})):
                    if loc_tech.get('results',{'energy_cap_equals':0}).get('energy_cap_equals',0) != 0 or\
                            loc_tech.get('results',{'storage_cap_equals':0}).get('storage_cap_equals',0) != 0:
                        loc_tech_b = copy.deepcopy(loc_tech)
                        built_tech_names.append(t)

                        if 'constraints' in loc_tech_b:
                            [loc_tech_b['constraints'].pop(c) for c in ['energy_cap_max', 'storage_cap_max'] if c in loc_tech_b['constraints']]
                        else:
                            loc_tech_b['constraints'] = {}
                        if 'energy_cap_equals' in loc_tech['results']:
                            loc_tech_b['constraints']['energy_cap_equals'] = loc_tech['results']['energy_cap_equals']
                        if 'storage_cap_equals' in loc_tech['results']:
                            loc_tech_b['constraints']['storage_cap_equals'] = loc_tech['results']['storage_cap_equals']
                        cost_classes = [c for c in loc_tech_b.keys() if 'costs.' in c]
                        for cost in cost_classes:
                            [loc_tech_b[cost].pop(c) for c in ['energy_cap','interest_rate','storage_cap'] if c in loc_tech_b[cost]]
                        loc_tech_b.pop('results')

                        if new_loc_tech and 'constraints' in new_loc_tech:
                            new_energy_cap_min = new_loc_tech['constraints'].get('energy_cap_min',new_tech.get('constraints',{}).get('energy_cap_min',0))
                            new_energy_cap_max = new_loc_tech['constraints'].get('energy_cap_max',new_tech.get('constraints',{}).get('energy_cap_max',0))
                            new_storage_cap_min = new_loc_tech['constraints'].get('storage_cap_min',new_tech.get('constraints',{}).get('storage_cap_min',0))
                            new_storage_cap_max = new_loc_tech['constraints'].get('storage_cap_max',new_tech.get('constraints',{}).get('storage_cap_max',0))
                        else:
                            new_energy_cap_min = new_tech.get('constraints',{}).get('energy_cap_min',0)
                            new_energy_cap_max = new_tech.get('constraints',{}).get('energy_cap_max',0)
                            new_storage_cap_min = new_tech.get('constraints',{}).get('storage_cap_min',0)
                            new_storage_cap_max = new_tech.get('constraints',{}).get('storage_cap_max',0)

                        if new_loc_tech == None:
                                new_loc_tech = {}
                        if 'constraints' not in new_loc_tech:
                                new_loc_tech['constraints'] = {}

                        if new_energy_cap_min > 0 and new_energy_cap_min-loc_tech['results']['energy_cap_equals'] > 0:
                            new_loc_tech['constraints']['energy_cap_min'] = new_energy_cap_min-loc_tech['results']['energy_cap_equals']
                            if new_loc_tech['constraints']['energy_cap_min'] < 0:
                                new_loc_tech['constraints']['energy_cap_min'] = 0
                        if new_energy_cap_max != 'inf' and new_energy_cap_max > 0:
                            new_loc_tech['constraints']['energy_cap_max'] = new_energy_cap_max-loc_tech['results']['energy_cap_equals']
                            if new_loc_tech['constraints']['energy_cap_max'] < 0:
                                new_loc_tech['constraints']['energy_cap_max'] = 0
                        if new_storage_cap_min > 0 and new_storage_cap_min-loc_tech['results']['storage_cap_equals'] > 0:
                            new_loc_tech['constraints']['storage_cap_min'] = new_storage_cap_min-loc_tech['results']['storage_cap_equals']
                            if new_loc_tech['constraints']['storage_cap_min'] < 0:
                                new_loc_tech['constraints']['storage_cap_min'] = 0
                        if new_storage_cap_max != 'inf' and new_storage_cap_max > 0:
                            new_loc_tech['constraints']['storage_cap_max'] = new_storage_cap_max-loc_tech['results']['storage_cap_equals']
                            if new_loc_tech['constraints']['storage_cap_max'] < 0:
                                new_loc_tech['constraints']['storage_cap_max'] = 0

                        new_loctechs['locations'][l]['techs'][t] = new_loc_tech                        
                        for x in loc_tech_b:
                            for y in loc_tech_b[x].keys():
                                # Copy over timeseries files for old techs, updating year to match new year
                                if 'file=' in str(loc_tech_b[x][y]):
                                    filename=loc_tech_b[x][y].replace('file=','').replace('.csv:value','')
                                    ts_df = pd.read_csv(old_inputs+'/'+filename+'.csv')
                                    ts_df['Unnamed: 0'] = pd.to_datetime(ts_df['Unnamed: 0'])
                                    freq = pd.infer_freq(ts_df['Unnamed: 0'])
                                    if not calendar.isleap(new_year):
                                        feb_29_mask = (ts_df['Unnamed: 0'].dt.month == 2) & (ts_df['Unnamed: 0'].dt.day == 29)
                                        ts_df = ts_df[~feb_29_mask]
                                        ts_df.index = ts_df['Unnamed: 0'].apply(lambda x: x.replace(year=new_year))
                                        ts_df.drop(columns=['Unnamed: 0'], inplace=True)
                                    elif not calendar.isleap(old_year):
                                        ts_df.index = ts_df['Unnamed: 0'].apply(lambda x: x.replace(year=new_year))
                                        ts_df.drop(columns=['Unnamed: 0'], inplace=True)
                                        idx = pd.date_range(ts_df.index.min(),ts_df.index.max(),freq=freq)
                                        ts_df = ts_df.reindex(idx, fill_value=0)

                                        # Leap Year Handling (Fill w/ Feb 28th)
                                        feb_28_mask = (ts_df.index.month == 2) & (ts_df.index.day == 28)
                                        feb_29_mask = (ts_df.index.month == 2) & (ts_df.index.day == 29)
                                        feb_28 = ts_df.loc[feb_28_mask, 'value'].values
                                        feb_29 = ts_df.loc[feb_29_mask, 'value'].values
                                        if ((len(feb_29) > 0) & (len(feb_28) > 0)):
                                            ts_df.loc[feb_29_mask, 'value'] = feb_28
                                    else:
                                        ts_df.index = ts_df['Unnamed: 0'].apply(lambda x: x.replace(year=new_year))
                                        ts_df.drop(columns=['Unnamed: 0'], inplace=True)
                                    ts_df.index.name = None
                                    ts_df.to_csv(os.path.join(new_inputs,filename+'-'+str(old_year)+'.csv'),index=True)
                                    loc_tech_b[x][y] = 'file='+filename+'-'+str(old_year)+'.csv:value'

                        if l not in built_loc_techs:
                            built_loc_techs[l] = {}
                        built_loc_techs[l][t+'_'+str(old_year)] = loc_tech_b

                        new_loctechs['locations'][l]['techs'][t+'_'+str(old_year)] = loc_tech_b
    for t in built_tech_names:
        tech = old_model['techs'][t]

        tech_b = copy.deepcopy(tech)
        if 'constraints' in tech_b:
            [tech_b['constraints'].pop(c) for c in ['energy_cap_max', 'storage_cap_max'] if c in tech_b['constraints']]
        cost_classes = [c for c in tech_b.keys() if 'costs.' in c]
        for cost in cost_classes:
            [tech_b[cost].pop(c) for c in ['energy_cap','interest_rate','storage_cap'] if c in tech_b[cost]]
            if len(tech_b[cost].keys()) == 0:
                tech_b.pop(cost)
        
        tech_b['essentials']['name'] += ' '+str(old_year)

        for x in tech_b:
            for y in tech_b[x].keys():
                # Copy over timeseries files for old techs, updating year to match new year
                if 'file=' in str(tech_b[x][y]):
                    filename=tech_b[x][y].replace('file=','').replace('.csv:value','')
                    ts_df = pd.read_csv(old_inputs+'/'+filename+'.csv')
                    ts_df['Unnamed: 0'] = pd.to_datetime(ts_df['Unnamed: 0'])
                    freq = pd.infer_freq(ts_df['Unnamed: 0'])
                    if not calendar.isleap(new_year):
                        feb_29_mask = (ts_df['Unnamed: 0'].dt.month == 2) & (ts_df['Unnamed: 0'].dt.day == 29)
                        ts_df = ts_df[~feb_29_mask]
                        ts_df.index = ts_df['Unnamed: 0'].apply(lambda x: x.replace(year=new_year))
                        ts_df.drop(columns=['Unnamed: 0'], inplace=True)
                    elif not calendar.isleap(old_year):
                        ts_df.index = ts_df['Unnamed: 0'].apply(lambda x: x.replace(year=new_year))
                        ts_df.drop(columns=['Unnamed: 0'], inplace=True)
                        idx = pd.date_range(ts_df.index.min(),ts_df.index.max(),freq=freq)
                        ts_df = ts_df.reindex(idx, fill_value=0)

                        # Leap Year Handling (Fill w/ Feb 28th)
                        feb_28_mask = (ts_df.index.month == 2) & (ts_df.index.day == 28)
                        feb_29_mask = (ts_df.index.month == 2) & (ts_df.index.day == 29)
                        feb_28 = ts_df.loc[feb_28_mask, 'value'].values
                        feb_29 = ts_df.loc[feb_29_mask, 'value'].values
                        if ((len(feb_29) > 0) & (len(feb_28) > 0)):
                            ts_df.loc[feb_29_mask, 'value'] = feb_28
                    else:
                        ts_df.index = ts_df['Unnamed: 0'].apply(lambda x: x.replace(year=new_year))
                        ts_df.drop(columns=['Unnamed: 0'], inplace=True)
                    ts_df.index.name = None
                    ts_df.to_csv(os.path.join(new_inputs,filename+'-'+str(old_year)+'.csv'),index=True)
                    tech_b[x][y] = 'file='+filename+'-'+str(old_year)+'.csv:value'
        built_techs[t+'_'+str(old_year)] = tech_b
        new_techs['techs'][t+'_'+str(old_year)] = tech_b

        if new_model['model']['group_share']:
            group_share = new_model['model']['group_share'].copy()
            for g in group_share:
                if t in g:
                    new_model['model']['group_share'][g+','+t+'_'+str(old_year)] = group_share[g]
                    new_model['model']['group_share'].pop(g)

        if new_model['group_constraints']:
            group_constraints = new_model['group_constraints'].copy()
            for g,c in group_constraints.items():
                if t in c.get('techs',[]) and t+'_'+str(old_year) not in c.get('techs',[]):
                    new_model['group_constraints'][g]['techs'].append(t+'_'+str(old_year))
                if t in c.get('techs_lhs',[]) and t+'_'+str(old_year) not in c.get('techs',[]):
                    new_model['group_constraints'][g]['techs_lhs'].append(t+'_'+str(old_year))
                if t in c.get('techs_rhs',[]) and t+'_'+str(old_year) not in c.get('techs',[]):
                    new_model['group_constraints'][g]['techs_rhs'].append(t+'_'+str(old_year))

    with open(new_inputs+'/techs.yaml','w') as outfile:
        yaml.dump(new_techs,outfile,default_flow_style=False)

    with open(new_inputs+'/locations.yaml','w') as outfile:
        yaml.dump(new_loctechs,outfile,default_flow_style=False)

    with open(new_inputs+'/model.yaml', 'w') as outfile:
        yaml.dump(new_model,outfile,default_flow_style=False)