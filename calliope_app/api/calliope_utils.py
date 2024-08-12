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


def get_model_yaml_set(run, scenario_id, year, tech_params_source, node_params_source):
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
    for param in run.run_options:
        logger.info(param)
        unique_param = param["root"] + '.' + param["name"]
        key_list = unique_param.split('.')
        dictify(model_yaml_set,key_list,param["value"])

    if node_params_source or tech_params_source:
        model_yaml_set["data_sources"] = {}
        if tech_params_source:
            model_yaml_set["data_sources"]["Tech_Timeseries"] = {
                "source": tech_params_source,
                "rows": "timeseries",
                "columns": ["techs", "parameters"]
            }
        if node_params_source:
            model_yaml_set["data_sources"]["Node_Timeseries"] = {
                "source": node_params_source,
                "rows": "timeseries",
                "columns": ["techs", "nodes", "parameters"]
            }
    
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
        param_list = ['nodes', loc.name]
        dictify(location_coord_yaml_set,param_list+['latitude'],loc.latitude)
        dictify(location_coord_yaml_set,param_list+['longitude'],loc.longitude)
        # Available Area
        if loc.available_area is None:
            continue
        param_list = ['nodes', loc.name,
                      'available_area']
        dictify(location_coord_yaml_set,param_list,loc.available_area)
    return location_coord_yaml_set


def get_techs_yaml_set(scenario_id, year):
    """ Function pulls tech parameters from Database for YAML """
    loc_techs = Scenario_Loc_Tech.objects.filter(scenario_id=scenario_id)
    tech_ids = list(loc_techs.values_list('loc_tech__technology',
                                          flat=True).distinct())
    parameters = Tech_Param.objects.filter(technology_id__in=tech_ids,
                                           year__lte=year, timeseries=False).order_by('-year')
    # Initialize the Return list
    techs_yaml_set = {}
    # Loop over Technologies
    for tech_id in tech_ids:
        params = parameters.filter(technology_id=tech_id)
        # Tracks which parameters have already been set (prioritized by year)
        unique_params = []
        # Loop over Parameters
        for param in params:
            param_keys = param.parameter.root.split('.')+[param.parameter.name]

            if param.technology.abstract_tech.name == 'transmission':
                parent_type = 'tech_groups'
            else:
                parent_type = 'techs'
            if param.parameter.index and param.parameter.dim:
                unique_param = param.parameter.root+'.'+param.parameter.name+str(param.parameter.index)+str(param.parameter.dim)
            else:
                unique_param = param.parameter.root+'.'+param.parameter.name
                
            if unique_param not in unique_params:
                # If parameter hasn't been set, add to Return List
                unique_params.append(unique_param)
                if '%' in param.parameter.units:  # Calliope in decimal format
                    value = float(param.value) / 100
                else:
                    value = param.value
                param_list = [parent_type, param.technology.calliope_name]+param_keys
                
                dictify(techs_yaml_set,param_list,value,param.parameter.index,param.parameter.dim)
    return techs_yaml_set


def get_loc_techs_yaml_set(scenario_id, year):
    """ Function pulls location technology (nodes)
    parameters from Database for YAML """
    loc_techs = Scenario_Loc_Tech.objects.filter(scenario_id=scenario_id)
    loc_tech_ids = list(loc_techs.values_list('loc_tech_id',
                                              flat=True).distinct())
    parameters = Loc_Tech_Param.objects.filter(
        loc_tech_id__in=loc_tech_ids, year__lte=year, timeseries=False).order_by('-year')
    # Initialize the Return list
    loc_techs_yaml_set = {}
    # Loop over Technologies
    for loc_tech_id in loc_tech_ids:
        loc_tech = Loc_Tech.objects.get(id=loc_tech_id)
        params = parameters.filter(loc_tech=loc_tech)
        parent = loc_tech.technology.abstract_tech.name

        technology = loc_tech.technology.calliope_name
        if parent == 'transmission':
            parent_type = 'links'
            location = \
                loc_tech.location_1.name + '_' + \
                loc_tech.location_2.name + '_' + \
                loc_tech.technology.calliope_name
            param_list = [parent_type, location]
            dictify(loc_techs_yaml_set,param_list+['from'],loc_tech.location_1.name)
            dictify(loc_techs_yaml_set,param_list+['to'],loc_tech.location_2.name)
            dictify(loc_techs_yaml_set,param_list+['inherit'],technology)
        else:
            parent_type = 'nodes'
            location = loc_tech.location_1.name

            if len(params) == 0:            
                param_list = [parent_type, location, 'techs',
                            technology]
                dictify(loc_techs_yaml_set,param_list,'')
                continue

        # Tracks which parameters have already been set (prioritized by year)
        unique_params = []
        # Loop over Parameters
        for param in params:
            param_keys = param.parameter.root.split('.')+[param.parameter.name]
            if param.parameter.index and param.parameter.dim:
                unique_param = param.parameter.root+'.'+param.parameter.name+str(param.parameter.index)+str(param.parameter.dim)
            else:
                unique_param = param.parameter.root+'.'+param.parameter.name
            unique_param = param.parameter.root+'.'+param.parameter.name
            if unique_param not in unique_params:
                if '%' in param.parameter.units:  # Calliope in decimal format
                    value = float(param.value) / 100
                else:
                    value = param.value

                if parent_type == 'links':
                    param_list = [parent_type, location]+param_keys
                else:
                    param_list = [parent_type, location, 'techs',
                                param.loc_tech.technology.calliope_name]+param_keys
                dictify(loc_techs_yaml_set,param_list,value,param.parameter.index,param.parameter.dim)
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


'''# This function takes a target dict and adds a new entry from an array of nested dict keys
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
                target[keys[-1]] = value'''

# This function takes a target dict and adds a new entry from an array of nested dict keys
# The final value in the array is the entry value and the rest of the list is the nested keys
# Creates any missing keys in the nested list
# This version of the function uses index and dimension values to create/add to a Calliope indexed parameter (introduced in v0.7)
# Multiple Engage parameter records can be added to the same indexed parameter in the YAML
def dictify(target, keys, value, index=None, dim=None):
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
            value = None
    elif value == 'True':
            value = True
    elif value == 'False':
            value = False
    else:
        # Try converting string to JSON object or float before saving as flat string
        try:
            string = value.replace(", ", ",")
            for char in ['\'', '“', '”', '‘', '’']:
                string = string.replace(char, '\"')
            value = json.loads(string)
        except Exception:
            try:
                value = float(value)
            except ValueError:
                value = value

    if index and dim:
        if len(index) == 1:
            index = index[0]
        if len(dim) == 1:
            dim = dim[0]

        if keys[-1] not in target:
            target[keys[-1]] = {}
        if 'data' not in target[keys[-1]]:
            target[keys[-1]]['data'] = []
            target[keys[-1]]['index'] = []
            target[keys[-1]]['dims'] = [dim]

        if [dim] != target[keys[-1]]['dims']:
            raise ValueError('Error with indexed parameter: {}. Dimensions do not match. {} vs {}'.format(keys[-1],[dim],target[keys[-1]]['dims']))
        
        target[keys[-1]]['data'] += [value]
        target[keys[-1]]['index'] += [index]
    else:
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

def _yaml_outputs(inputs_dir, outputs_dir):
    results_var = {'flow_cap':'results_flow_cap.csv','storage_cap':'results_storage_cap.csv'}
    
    model = yaml.load(open(os.path.join(inputs_dir,'model.yaml')), Loader=yaml.FullLoader)
    model.update(yaml.load(open(os.path.join(inputs_dir,'locations.yaml')), Loader=yaml.FullLoader))
    model.update(yaml.load(open(os.path.join(inputs_dir,'techs.yaml')), Loader=yaml.FullLoader))

    has_outputs = False
    for v in results_var.keys():
        if not os.path.exists(os.path.join(outputs_dir,results_var[v])):
            continue
        has_outputs = True
        r_df = pd.read_csv(os.path.join(outputs_dir,results_var[v]))

        for l in model['nodes'].keys():
            if 'techs' in model['nodes'][l].keys():
                for t in model['nodes'][l]['techs'].keys():
                    if v == 'storage_cap' and model['techs'][t]['base_tech'] not in ['storage','supply_plus']:
                        continue
                    if model['nodes'][l]['techs'][t] == None:
                        model['nodes'][l]['techs'][t] = {}
                    if 'results' not in model['nodes'][l]['techs'][t]:
                        model['nodes'][l]['techs'][t]['results'] = {}
                    model['nodes'][l]['techs'][t]['results'][v+'_equals'] = float(r_df.loc[(r_df['nodes'] == l) &
                                                                        (r_df['techs'] == t)][v].values[0])  
        for l in model['links'].keys():
            l1 = model['links'][l]['from']
            l2 = model['links'][l]['to']
            if model['links'][l] == None:
                model['links'][l] = {}
            if 'results' not in model['links'][l]:
                model['links'][l]['results'] = {}
            model['links'][l]['results'][v+'_equals'] = float(r_df.loc[(r_df['nodes'] == l1) &
                                                                (r_df['techs'] == t)][v].values[0])
    if has_outputs:
        yaml.dump(model, open(os.path.join(outputs_dir,'model_results.yaml'),'w+'), default_flow_style=False)

def apply_gradient(old_inputs,old_results,new_inputs,old_year,new_year):
    old_model = yaml.safe_load(open(old_results+'/model_results.yaml'))

    new_techs = yaml.safe_load(open(new_inputs+'/techs.yaml','r'))
    new_loctechs = yaml.safe_load(open(new_inputs+'/locations.yaml','r'))
    new_model = yaml.safe_load(open(new_inputs+'/model.yaml','r'))

    built_techs = {'techs':{},'tech_groups':{}}
    built_loc_techs = {}

    for l in old_model['nodes']:
        if 'techs' in old_model['nodes'][l]:
            for t in old_model['nodes'][l]['techs']:
                old_tech = old_model['techs'][t]
                if t not in new_techs['techs']:
                    continue
                new_tech = new_techs['techs'][t]
                new_loc_tech = new_loctechs['nodes'][l]['techs'][t]
                loc_tech = old_model['nodes'][l]['techs'][t]
                if ('flow_cap_max' in loc_tech or 'storage_cap_max' in loc_tech) or\
                        ('flow_cap_max' in old_tech or 'storage_cap_max' in old_tech):
                    if loc_tech.get('results',{'flow_cap_equals':0}).get('flow_cap_equals',0) != 0 or\
                            loc_tech.get('results',{'storage_cap_equals':0}).get('storage_cap_equals',0) != 0:
                        loc_tech_b = copy.deepcopy(loc_tech)

                        # Record built techs and the total systemwide capacity of those techs to use with flow_cap_max_systemwide
                        if t in built_techs['techs']:
                            built_techs['techs'][t] += loc_tech.get('results',{'flow_cap_equals':0}).get('flow_cap_equals',0)
                        else:
                            built_techs['techs'][t] = loc_tech.get('results',{'flow_cap_equals':0}).get('flow_cap_equals',0)

                        [loc_tech_b.pop(c) for c in ['flow_cap_max', 'storage_cap_max'] if c in loc_tech_b]
                        if 'flow_cap_equals' in loc_tech['results']:
                            loc_tech_b['flow_cap_min'] = loc_tech['results']['flow_cap_equals']
                            loc_tech_b['flow_cap_max'] = loc_tech['results']['flow_cap_equals']
                        if 'storage_cap_equals' in loc_tech['results']:
                            loc_tech_b['storage_cap_equals'] = loc_tech['results']['storage_cap_equals']
                        [loc_tech_b.pop(c) for c in ['cost_flow_cap','cost_interest_rate','cost_storage_cap'] if c in loc_tech_b]
                        loc_tech_b.pop('results')

                        if new_loc_tech:
                            new_flow_cap_min = new_loc_tech.get('flow_cap_min',new_tech.get('flow_cap_min',0))
                            new_flow_cap_max = new_loc_tech.get('flow_cap_max',new_tech.get('flow_cap_max',0))
                            new_storage_cap_min = new_loc_tech.get('storage_cap_min',new_tech.get('storage_cap_min',0))
                            new_storage_cap_max = new_loc_tech.get('storage_cap_max',new_tech.get('storage_cap_max',0))
                        else:
                            new_flow_cap_min = new_tech.get('flow_cap_min',0)
                            new_flow_cap_max = new_tech.get('flow_cap_max',0)
                            new_storage_cap_min = new_tech.get('storage_cap_min',0)
                            new_storage_cap_max = new_tech.get('storage_cap_max',0)

                        if new_loc_tech == None:
                            new_loc_tech = {}

                        if new_flow_cap_min > 0 and new_flow_cap_min-loc_tech['results']['flow_cap_equals'] > 0:
                            new_loc_tech['flow_cap_min'] = new_flow_cap_min-loc_tech['results']['flow_cap_equals']
                            if new_loc_tech['flow_cap_min'] < 0:
                                new_loc_tech['flow_cap_min'] = 0
                        if new_flow_cap_max != 'inf' and new_flow_cap_max > 0:
                            new_loc_tech['flow_cap_max'] = new_flow_cap_max-loc_tech['results']['flow_cap_equals']
                            if new_loc_tech['flow_cap_max'] < 0:
                                new_loc_tech['flow_cap_max'] = 0
                        if new_storage_cap_min > 0 and new_storage_cap_min-loc_tech['results']['storage_cap_equals'] > 0:
                            new_loc_tech['storage_cap_min'] = new_storage_cap_min-loc_tech['results']['storage_cap_equals']
                            if new_loc_tech['storage_cap_min'] < 0:
                                new_loc_tech['storage_cap_min'] = 0
                        if new_storage_cap_max != 'inf' and new_storage_cap_max > 0:
                            new_loc_tech['storage_cap_max'] = new_storage_cap_max-loc_tech['results']['storage_cap_equals']
                            if new_loc_tech['storage_cap_max'] < 0:
                                new_loc_tech['storage_cap_max'] = 0

                        new_loctechs['nodes'][l]['techs'][t] = new_loc_tech

                        built_loc_techs[l+t] = loc_tech_b

                        new_loctechs['nodes'][l]['techs'][t+'_'+str(old_year)] = loc_tech_b

    for l in old_model['links']:
        t = old_model['links'][l]['inherit']
        old_tech = old_model['tech_groups'][t]
        if t not in new_techs['tech_groups']:
            continue
        new_tech = new_techs['tech_groups'][t]
        new_loc_tech = new_loctechs['links'][l]
        loc_tech = old_model['links'][l]
        if ('flow_cap_max' in loc_tech or 'storage_cap_max' in loc_tech) or\
                ('flow_cap_max' in old_tech or 'storage_cap_max' in old_tech):
            if loc_tech.get('results',{'flow_cap_equals':0}).get('flow_cap_equals',0) != 0 or\
                    loc_tech.get('results',{'storage_cap_equals':0}).get('storage_cap_equals',0) != 0:
                loc_tech_b = copy.deepcopy(loc_tech)

                # Record built techs and the total systemwide capacity of those techs to use with flow_cap_max_systemwide
                if t in built_techs['tech_groups']:
                    built_techs['tech_groups'][t] += loc_tech.get('results',{'flow_cap_equals':0}).get('flow_cap_equals',0)
                else:
                    built_techs['tech_groups'][t] = loc_tech.get('results',{'flow_cap_equals':0}).get('flow_cap_equals',0)

                [loc_tech_b.pop(c) for c in ['flow_cap_max', 'storage_cap_max'] if c in loc_tech_b]
                if 'flow_cap_equals' in loc_tech['results']:
                    loc_tech_b['flow_cap_min'] = loc_tech['results']['flow_cap_equals']
                    loc_tech_b['flow_cap_max'] = loc_tech['results']['flow_cap_equals']
                if 'storage_cap_equals' in loc_tech['results']:
                    loc_tech_b['storage_cap_equals'] = loc_tech['results']['storage_cap_equals']
                [loc_tech_b.pop(c) for c in ['cost_flow_cap','cost_interest_rate','cost_storage_cap'] if c in loc_tech_b]
                loc_tech_b.pop('results')

                if new_loc_tech:
                    new_flow_cap_min = new_loc_tech.get('flow_cap_min',new_tech.get('flow_cap_min',0))
                    new_flow_cap_max = new_loc_tech.get('flow_cap_max',new_tech.get('flow_cap_max',0))
                    new_storage_cap_min = new_loc_tech.get('storage_cap_min',new_tech.get('storage_cap_min',0))
                    new_storage_cap_max = new_loc_tech.get('storage_cap_max',new_tech.get('storage_cap_max',0))
                else:
                    new_flow_cap_min = new_tech.get('flow_cap_min',0)
                    new_flow_cap_max = new_tech.get('flow_cap_max',0)
                    new_storage_cap_min = new_tech.get('storage_cap_min',0)
                    new_storage_cap_max = new_tech.get('storage_cap_max',0)

                if new_loc_tech == None:
                    new_loc_tech = {}

                if new_flow_cap_min > 0 and new_flow_cap_min-loc_tech['results']['flow_cap_equals'] > 0:
                    new_loc_tech['flow_cap_min'] = new_flow_cap_min-loc_tech['results']['flow_cap_equals']
                    if new_loc_tech['flow_cap_min'] < 0:
                        new_loc_tech['flow_cap_min'] = 0
                if new_flow_cap_max != 'inf' and new_flow_cap_max > 0:
                    new_loc_tech['flow_cap_max'] = new_flow_cap_max-loc_tech['results']['flow_cap_equals']
                    if new_loc_tech['flow_cap_max'] < 0:
                        new_loc_tech['flow_cap_max'] = 0
                if new_storage_cap_min > 0 and new_storage_cap_min-loc_tech['results']['storage_cap_equals'] > 0:
                    new_loc_tech['storage_cap_min'] = new_storage_cap_min-loc_tech['results']['storage_cap_equals']
                    if new_loc_tech['storage_cap_min'] < 0:
                        new_loc_tech['storage_cap_min'] = 0
                if new_storage_cap_max != 'inf' and new_storage_cap_max > 0:
                    new_loc_tech['storage_cap_max'] = new_storage_cap_max-loc_tech['results']['storage_cap_equals']
                    if new_loc_tech['storage_cap_max'] < 0:
                        new_loc_tech['storage_cap_max'] = 0

                new_loctechs['links'][l] = new_loc_tech

                built_loc_techs[l+t] = loc_tech_b

                loc_tech_b['inherit'] += '_'+str(old_year)

                new_loctechs['links'][l+'_'+str(old_year)] = loc_tech_b

    for level in built_techs.keys():
        for t in built_techs[level].keys():
            tech = old_model[level][t]
            tech_b = copy.deepcopy(tech)

            # Handle systemwide energy cap gradient
            if 'flow_cap_max_systemwide' in new_techs[level][t]:
                new_techs[level][t]['flow_cap_max_systemwide'] = max([new_techs[level][t]['flow_cap_max_systemwide']-built_techs[level][t],0])
            
            [tech_b.pop(c) for c in ['flow_cap_max', 'storage_cap_max'] if c in tech_b]
            [tech_b.pop(c) for c in ['cost_flow_cap','cost_interest_rate','cost_storage_cap'] if c in tech_b]
            
            tech_b['name'] += ' '+str(old_year)

            new_techs[level][t+'_'+str(old_year)] = tech_b

            '''if new_model['group_constraints']:
                group_constraints = new_model['group_constraints'].copy()
                for g,c in group_constraints.items():
                    if t in c.get('techs',[]) and t+'_'+str(old_year) not in c.get('techs',[]):
                        new_model['group_constraints'][g]['techs'].append(t+'_'+str(old_year))
                    if t in c.get('techs_lhs',[]) and t+'_'+str(old_year) not in c.get('techs',[]):
                        new_model['group_constraints'][g]['techs_lhs'].append(t+'_'+str(old_year))
                    if t in c.get('techs_rhs',[]) and t+'_'+str(old_year) not in c.get('techs',[]):
                        new_model['group_constraints'][g]['techs_rhs'].append(t+'_'+str(old_year))'''

    if os.path.exists(os.path.join(old_inputs,'node_params.csv')):
        node_ts_df_old = pd.read_csv(os.path.join(old_inputs,'node_params.csv'),header=[0,1,2],index_col=[0])
        keep_cols = [c[0]+c[1] not in built_loc_techs for c in node_ts_df_old.columns]
        node_ts_df_old.columns = pd.MultiIndex.from_tuples([(c[0],c[1]+'_'+str(old_year),c[2]) for c in node_ts_df_old.columns])
        node_ts_df_old = node_ts_df_old.loc[:,keep_cols]
        node_ts_df_old['ts','ts','ts'] = pd.to_datetime(node_ts_df_old.index)
        if not calendar.isleap(new_year):
            feb_29_mask = (node_ts_df_old['ts'].dt.month == 2) & (node_ts_df_old['ts'].dt.day == 29)
            node_ts_df_old = node_ts_df_old[~feb_29_mask]
            node_ts_df_old.index = node_ts_df_old['ts'].apply(lambda x: x.replace(year=new_year))
        elif not calendar.isleap(old_year):
            node_ts_df_old.index = node_ts_df_old['ts'].apply(lambda x: x.replace(year=new_year))

            # Leap Year Handling (Fill w/ Feb 28th)
            feb_28_mask = (node_ts_df_old.index.month == 2) & (node_ts_df_old.index.day == 28)
            feb_29_mask = (node_ts_df_old.index.month == 2) & (node_ts_df_old.index.day == 29)
            feb_28 = node_ts_df_old.loc[feb_28_mask].values
            feb_29 = node_ts_df_old.loc[feb_29_mask].values
            if ((len(feb_29) > 0) & (len(feb_28) > 0)):
                node_ts_df_old.loc[feb_29_mask] = feb_28

        node_ts_df_old.drop(columns=['ts','ts','ts'],inplace=True)
    
        if os.path.exists(os.path.join(new_inputs,'node_params.csv')):
            node_ts_df_new = pd.read_csv(os.path.join(new_inputs,'node_params.csv'),header=[0,1],index_col=[0])
            node_ts_df_new.index = pd.to_datetime(node_ts_df_new.index)
            node_ts_df_new = pd.concat([node_ts_df_new,node_ts_df_old],axis=1)
        else:
            new_model['data_sources']['Node_Timeseries'] = {'source': 'node_params.csv', 'rows': 'timesteps',
                                                                'columns': ['nodes', 'techs', 'parameters']}
            node_ts_df_new = node_ts_df_old
        node_ts_df_new.index.name = None
        node_ts_df_new.to_csv(os.path.join(new_inputs,'node_params.csv'))

    if os.path.exists(os.path.join(old_inputs,'tech_params.csv')):
        tech_ts_df_old = pd.read_csv(os.path.join(old_inputs,'tech_params.csv'),header=[0,1],index_col=[0])
        keep_cols = [c[0] in built_techs for c in tech_ts_df_old.columns]
        tech_ts_df_old.columns = pd.MultiIndex.from_tuples([(c[0]+'_'+str(old_year),c[1]) for c in tech_ts_df_old.columns])
        tech_ts_df_old = tech_ts_df_old.loc[:,keep_cols]
        tech_ts_df_old['ts','ts'] = pd.to_datetime(tech_ts_df_old.index)
        if not calendar.isleap(new_year):
            feb_29_mask = (tech_ts_df_old['ts','ts'].dt.month == 2) & (tech_ts_df_old['ts','ts'].dt.day == 29)
            tech_ts_df_old = tech_ts_df_old[~feb_29_mask]
            tech_ts_df_old.index = tech_ts_df_old['ts','ts'].apply(lambda x: x.replace(year=new_year))
        elif not calendar.isleap(old_year):
            tech_ts_df_old.index = tech_ts_df_old['ts','ts'].apply(lambda x: x.replace(year=new_year))

            # Leap Year Handling (Fill w/ Feb 28th)
            feb_28_mask = (tech_ts_df_old.index.month == 2) & (tech_ts_df_old.index.day == 28)
            feb_29_mask = (tech_ts_df_old.index.month == 2) & (tech_ts_df_old.index.day == 29)
            feb_28 = tech_ts_df_old.loc[feb_28_mask].values
            feb_29 = tech_ts_df_old.loc[feb_29_mask].values
            if ((len(feb_29) > 0) & (len(feb_28) > 0)):
                tech_ts_df_old.loc[feb_29_mask] = feb_28

        tech_ts_df_old.drop(columns=['ts','ts'],inplace=True)
    
        if os.path.exists(os.path.join(new_inputs,'tech_params.csv')):
            tech_ts_df_new = pd.read_csv(os.path.join(new_inputs,'tech_params.csv'),header=[0,1],index_col=[0])
            tech_ts_df_new.index = pd.to_datetime(tech_ts_df_old.index)
            tech_ts_df_new = pd.concat([tech_ts_df_new,tech_ts_df_old],axis=1)
        else:
            new_model['data_sources']['Tech_Timeseries'] = {'source': 'tech_params.csv', 'rows': 'timesteps',
                                                                'columns': ['techs', 'parameters']}
            tech_ts_df_new = tech_ts_df_old
        tech_ts_df_new.index.name = None
        tech_ts_df_new.to_csv(os.path.join(new_inputs,'tech_params.csv'))

    with open(new_inputs+'/techs.yaml','w') as outfile:
        yaml.dump(new_techs,outfile,default_flow_style=False)

    with open(new_inputs+'/locations.yaml','w') as outfile:
        yaml.dump(new_loctechs,outfile,default_flow_style=False)

    with open(new_inputs+'/model.yaml', 'w') as outfile:
        yaml.dump(new_model,outfile,default_flow_style=False)