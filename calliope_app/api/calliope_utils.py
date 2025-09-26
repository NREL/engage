"""
This module contains support functions and libraries used in
interfacing with Calliope.
"""

import os
import yaml
import shutil
from calliope import Model as CalliopeModel
from calliope import read_yaml as calliope_read_yaml
import pandas as pd
import json
import copy
import calendar

from api.models.configuration import Scenario_Param, Scenario_Loc_Tech, \
    Location, Tech_Param, Loc_Tech_Param, Loc_Tech, Scenario, Carrier, Run_Parameter
from api.models.outputs import Run
import logging


logger = logging.getLogger(__name__)


def get_model_yaml_set(run, scenario_id, year, ts_files):
    """ Function pulls model parameters from Database for YAML """
    params = Scenario_Param.objects.filter(scenario_id=scenario_id,
                                           year__lte=year, run_parameter__mode__contains=[run.mode]).order_by('-year')
    # Initialize the Return list
    model_yaml_set = {}
    # Tracks which parameters have already been set (prioritized by year)
    unique_params = []
    # Loop over Parameters
    for param in params:
        if param.run_parameter.root in ['constraints','global_expressions','parameters','dimensions','lookups','variables','piecewise_constraints']:
            continue
        unique_param = param.run_parameter.root+'.'+param.run_parameter.name

        # NOTE: deprecated run parameter in the database
        if unique_param == "run.objective_options":
            continue
        
        if unique_param not in unique_params:
            # If parameter hasn't been set, add to Return List
            unique_params.append(unique_param)
            key_list = unique_param.split('.')
            dictify(model_yaml_set,key_list,param.value)
    dictify(model_yaml_set,['import'],'["techs.yaml","locations.yaml"]',simplify=False)
    dictify(model_yaml_set,['config','init','math_paths','custom_math'],'custom_math.yaml',simplify=False)
    if run.mode == 'operate':
        dictify(model_yaml_set,['config','init','extra_math'],'["milp","operate","custom_math"]',simplify=False)
    else:
        dictify(model_yaml_set,['config','init','extra_math'],'["milp","custom_math"]',simplify=False)
    for run_param in run.run_options:
        unique_param = run_param['root'] + '.' + run_param['name']
        key_list = unique_param.split('.')
        dictify(model_yaml_set,key_list,run_param['value'])

    if ts_files:
        model_yaml_set["data_tables"] = {}
        
        for dims, fname in ts_files.items():
            model_yaml_set["data_tables"]["_".join(dims)+"_timeseries"] = {
                "data": fname,
                "rows": "timesteps",
                "columns": list(dims)
            }
    
    return model_yaml_set

def get_custom_math_yaml_set(run, scenario_id, year):
    """ Function pulls model parameters from Database for YAML """
    params = Scenario_Param.objects.filter(scenario_id=scenario_id,
                                           year__lte=year,run_parameter__root__in=['constraints','global_expressions','parameters','dimensions','lookups','variables','piecewise_constraints'],
                                           run_parameter__mode__contains=[run.mode]).order_by('-year')

    # Initialize the Return list
    custom_math_yaml_set = {}
    # Tracks which parameters have already been set (prioritized by year)
    unique_params = []
    # Loop over Parameters
    for param in params:
        unique_param = param.run_parameter.id

        if unique_param not in unique_params:
            # If parameter hasn't been set, add to Return List
            unique_params.append(unique_param)
            key_list = param.run_parameter.root.split('.')
            dictify(custom_math_yaml_set,key_list,param.value,True)

    return custom_math_yaml_set

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
        if 'techs' not in location_coord_yaml_set['nodes'][loc.name]:
            dictify(location_coord_yaml_set,param_list+['techs'],'')
        # Available Area
        if loc.available_area is None:
            continue
        param_list = ['nodes', loc.name,
                      'available_area']
        dictify(location_coord_yaml_set,param_list,loc.available_area)
    return location_coord_yaml_set


def get_techs_yaml_set(run, scenario_id, year):
    """ Function pulls tech parameters from Database for YAML """
    loc_techs = Scenario_Loc_Tech.objects.filter(scenario_id=scenario_id)
    tech_ids = list(loc_techs.values_list('loc_tech__technology',
                                          flat=True).distinct())
    parameters = Tech_Param.objects.filter(technology_id__in=tech_ids,
                                           year__lte=year, timeseries=False, parameter__tags__contains=[run.mode+"_mode"]).order_by('-year')
    # Initialize the Return list
    techs_yaml_set = {}
    # Loop over Technologies
    for tech_id in tech_ids:
        params = parameters.filter(technology_id=tech_id)
        # Tracks which parameters have already been set (prioritized by year)
        unique_params = []
        # Loop over Parameters
        for param in params:
            if param.technology.abstract_tech.name == 'transmission':
                parent_type = 'templates'
            else:
                parent_type = 'techs'
            if (param.parameter.index and param.parameter.dim) or (param.index and param.dim):
                if not(param.parameter.index and param.parameter.dim):
                    index = param.index
                    dim = param.dim
                elif not(param.index and param.dim):
                    index = param.parameter.index
                    dim = param.parameter.dim
                else:
                    index = param.parameter.index+param.index
                    dim = param.parameter.dim+param.dim
            else:
                index = []
                dim = []
            # Handle piecewise parameters
            param_name = param.parameter.name
            if param.piecewise_dim:
                param_name = f'{param_name}_{param.piecewise_dim[0]}'
                dim += ['breakpoint']
                index += [int(param.piecewise_dim[1:])]
            unique_param = param.parameter.root+'.'+param_name+str(index)+str(dim)
            
                
            if unique_param not in unique_params:
                param_keys = param.parameter.root.split('.')+[param_name]

                # If parameter hasn't been set, add to Return List
                unique_params.append(unique_param)
                if '%' in param.parameter.units:  # Calliope in decimal format
                    value = float(param.value) / 100
                else:
                    value = param.value
                param_list = [parent_type, param.technology.calliope_name]+param_keys
                
                dictify(techs_yaml_set,param_list,value,index,dim)
    return techs_yaml_set


def get_loc_techs_yaml_set(run, scenario_id, year):
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
            parent_type = 'techs'
            location = \
                loc_tech.location_1.name + '_' + \
                loc_tech.location_2.name + '_' + \
                loc_tech.technology.calliope_name
            param_list = [parent_type, location]
            dictify(loc_techs_yaml_set,param_list+['link_from'],loc_tech.location_1.name)
            dictify(loc_techs_yaml_set,param_list+['link_to'],loc_tech.location_2.name)
            dictify(loc_techs_yaml_set,param_list+['template'],technology)
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
            if (param.parameter.index and param.parameter.dim) or (param.index and param.dim):
                if not(param.parameter.index and param.parameter.dim):
                    index = param.index
                    dim = param.dim
                elif not(param.index and param.dim):
                    index = param.parameter.index
                    dim = param.parameter.dim
                else:
                    index = param.parameter.index+param.index
                    dim = param.parameter.dim+param.dim
            else:
                index = []
                dim = []
            # Handle piecewise parameters
            param_name = param.parameter.name
            if param.piecewise_dim:
                param_name = f'{param_name}_{param.piecewise_dim[0]}'
                dim += ['breakpoint']
                index += [int(param.piecewise_dim[1:])]
            unique_param = param.parameter.root+'.'+param_name+str(index)+str(dim)
            if unique_param not in unique_params:
                param_keys = param.parameter.root.split('.')+[param_name]
                
                unique_params.append(unique_param)
                if '%' in param.parameter.units:  # Calliope in decimal format
                    value = float(param.value) / 100
                else:
                    value = param.value

                if parent_type == 'techs':
                    param_list = [parent_type, location]+param_keys
                else:
                    param_list = [parent_type, location, 'techs',
                                param.loc_tech.technology.calliope_name]+param_keys
                if 'multi_index' in param.parameter.tags:                  
                    try:
                        value_l = json.loads(value)
                    except:
                        dictify(loc_techs_yaml_set,param_list,value,index,dim)
                        value_l = []
                    if 'carrier_multiselect' in param.parameter.tags:
                        dim = 'carriers'
                    for v in value_l:
                        dictify(loc_techs_yaml_set,param_list,'True',v,dim)
                else:
                    dictify(loc_techs_yaml_set,param_list,value,index,dim)
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
def dictify(target, keys, value, index=None, dim=None, update=False, simplify=True):
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

    if simplify and type(value) == list and len(value) == 1:
        value = value[0]
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
            target[keys[-1]]['dims'] = dim

        if dim != target[keys[-1]]['dims']:
            raise ValueError('Error with indexed parameter: {}. Dimensions do not match. {} vs {}'.format(keys[-1],dim,target[keys[-1]]['dims']))
        
        target[keys[-1]]['data'] += [value]
        target[keys[-1]]['index'] += [index]
    elif update and target[keys[-1]]:
        target[keys[-1]] = {*target[keys[-1]], *value}
    else:
        target[keys[-1]] = value
    

def stringify(param_list):
    param_list = [str(x) for x in param_list]
    return '||'.join(param_list).replace('||||', '||')


def run_basic(model_path, logger):
    """ Basic Run """
    logger.info('--- Run Basic')
    model = calliope_read_yaml(model_path)
    logger.info(model.info())
    model.build()
    model.solve()
    _write_outputs(model, model_path)
    return model.runtime.termination_condition


def run_clustered(model_path, idx, logger):
    """ Clustered Capacity Expansion w/ Monthly Operational Runs """
    logger.info('--- Run Clustering')
    _set_clustering(model_path, on=True)
    _set_subset_time(model_path)
    _set_capacities(model_path)
    model = calliope_read_yaml(model_path)
    model.run()
    _write_outputs(model, model_path)
    if model.runtime.termination_condition != 'optimal':
        return model.runtime.termination_condition
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
            model = calliope_read_yaml(model_path)
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
        yaml.dump(model_yaml, file, default_flow_style=None)


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
        yaml.dump(model_yaml, file, default_flow_style=None)


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
        yaml.dump(model_yaml, file, default_flow_style=None)
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
                tech_data['constraints']['storage_cap'] = float(storage[key])
            locations_yaml['locations'][loc]['techs'][tech] = tech_data
    # Update Links Settings
    for loc, loc_data in locations_yaml['techs'].items():
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
        yaml.dump(locations_yaml, file, default_flow_style=None)


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
        _yaml_outputs(os.path.dirname(model_path),final_outputs)
    else:
        _yaml_outputs(os.path.dirname(model_path),save_outputs)

def _yaml_outputs(inputs_dir, outputs_dir):
    results_vars = {'flow_cap':'carriers','storage_cap':None,'area_use':None,'source_cap':None,'purchased_units':None}
    
    model = yaml.load(open(os.path.join(inputs_dir,'model.yaml')), Loader=yaml.FullLoader)
    techs = {}
    locations = {}
    if os.path.exists(os.path.join(inputs_dir,'techs.yaml')):
        techs = yaml.load(open(os.path.join(inputs_dir,'techs.yaml')), Loader=yaml.FullLoader)
    if os.path.exists(os.path.join(inputs_dir,'locations.yaml')):
        locations = yaml.load(open(os.path.join(inputs_dir,'locations.yaml')), Loader=yaml.FullLoader)
    
    keys = set(model.keys()) | set(techs.keys()) | set(locations.keys())
    combined_model = {}
    for key in keys:
        if type(model.get(key,{})) is not dict:
            combined_model[key] = model[key]
        else:
            combined_model[key] = {**model.get(key, {}),
                                **techs.get(key, {}),
                                **locations.get(key, {})}

    has_outputs = False
    for results_var, index in results_vars.items():
        if not os.path.exists(os.path.join(outputs_dir,'results_'+results_var+'.csv')):
            continue
        has_outputs = True
        r_df = pd.read_csv(os.path.join(outputs_dir,'results_'+results_var+'.csv'))

        for l in combined_model['nodes'].keys():
            if 'techs' in combined_model['nodes'][l].keys() and combined_model['nodes'][l]['techs']:
                for t in combined_model['nodes'][l]['techs'].keys():
                    if combined_model['nodes'][l]['techs'][t] is None:
                        combined_model['nodes'][l]['techs'][t] = {}
                    if 'results' not in combined_model['nodes'][l]['techs'][t]:
                        combined_model['nodes'][l]['techs'][t]['results'] = {}
                    if len(r_df.loc[(r_df['nodes'] == l) & (r_df['techs'] == t)][results_var]) != 0:
                        if index:
                            values = r_df.loc[(r_df['nodes'] == l) & (r_df['techs'] == t)][[index,results_var]]
                            combined_model['nodes'][l]['techs'][t]['results'][results_var] = {'data':list(values[results_var]),'index':list(values[index]),'dims':[index]}
                        else:
                            combined_model['nodes'][l]['techs'][t]['results'][results_var] = float(r_df.loc[(r_df['nodes'] == l) &
                                                                        (r_df['techs'] == t)][results_var].values[0])  
        for l in combined_model['techs'].keys():
            if 'link_from' in combined_model['techs'][l] and 'link_to' in combined_model['techs'][l]:
                l1 = combined_model['techs'][l]['link_from']
                l2 = combined_model['techs'][l]['link_to']
                if combined_model['techs'][l] is None:
                    combined_model['techs'][l] = {}
                if 'results' not in combined_model['techs'][l]:
                    combined_model['techs'][l]['results'] = {}
                if len(r_df.loc[(r_df['nodes'] == l1) & (r_df['techs'] == l)][results_var]) != 0:
                    if index:
                        values = r_df.loc[(r_df['nodes'] == l1) & (r_df['techs'] == l)][[index,results_var]]
                        combined_model['techs'][l]['results'][results_var] = {'data':list(values[results_var]),'index':list(values[index]),'dims':[index]}
                    else:
                        combined_model['techs'][l]['results'][results_var] = float(r_df.loc[(r_df['nodes'] == l1) &
                                                                    (r_df['techs'] == l)][results_var].values[0])
        yaml.dump(combined_model, open(os.path.join(outputs_dir,'model_results.yaml'),'w+'), default_flow_style=None)

def _operate_outputs(inputs_dir, outputs_dir, operate_dir, logger):
    results_vars = {'flow_cap':'carriers','storage_cap':None,'purchased_units':None} #'area_use':None,'source_cap':None,
    
    model = yaml.load(open(os.path.join(operate_dir,'model.yaml')), Loader=yaml.FullLoader)
    techs = {}
    locations = {}
    if os.path.exists(os.path.join(operate_dir,'techs.yaml')):
        techs = yaml.load(open(os.path.join(operate_dir,'techs.yaml')), Loader=yaml.FullLoader)
    if os.path.exists(os.path.join(operate_dir,'locations.yaml')):
        locations = yaml.load(open(os.path.join(operate_dir,'locations.yaml')), Loader=yaml.FullLoader)

    for results_var, index in results_vars.items():
        if not os.path.exists(os.path.join(outputs_dir,'results_'+results_var+'.csv')):
            continue
        r_df = pd.read_csv(os.path.join(outputs_dir,'results_'+results_var+'.csv'))

        for l in locations['nodes'].keys():
            if 'techs' in locations['nodes'][l].keys() and locations['nodes'][l]['techs']:
                for t in locations['nodes'][l]['techs'].keys():
                    if locations['nodes'][l]['techs'][t]:
                        locations['nodes'][l]['techs'][t].pop(results_var+'_min', None)
                        locations['nodes'][l]['techs'][t].pop(results_var+'_max', None)
                    elif locations['nodes'][l]['techs'][t] is None:
                        locations['nodes'][l]['techs'][t] = {}
                    if len(r_df.loc[(r_df['nodes'] == l) & (r_df['techs'] == t)][results_var]) != 0 and techs['techs'][t].get('base_tech') != 'demand':
                        if index:
                            values = r_df.loc[(r_df['nodes'] == l) & (r_df['techs'] == t)][[index,results_var]]
                            locations['nodes'][l]['techs'][t][results_var] = {'data':list(values[results_var]),'index':list(values[index]),'dims':[index]}
                        else:
                            locations['nodes'][l]['techs'][t][results_var] = float(r_df.loc[(r_df['nodes'] == l) &
                                                                        (r_df['techs'] == t)][results_var].values[0]) 
                        
                        # Operate mode needs cyclic_storage to be false
                        if results_var == 'storage_cap':
                            locations['nodes'][l]['techs'][t]['cyclic_storage'] = False
                        
        for lt in techs['templates'].keys():
            techs['templates'][lt].pop(results_var+'_min', None)
            techs['templates'][lt].pop(results_var+'_max', None)
            
        for t in locations['techs'].keys():
            if locations['techs'][t]:
                locations['techs'][t].pop(results_var+'_min', None)
                locations['techs'][t].pop(results_var+'_max', None)
            if 'link_from' in locations['techs'][t] and 'link_to' in locations['techs'][t]:
                l1 = locations['techs'][t]['link_from']
                l2 = locations['techs'][t]['link_to']
                if locations['techs'][t] is None:
                    locations['techs'][t] = {}
                if len(r_df.loc[(r_df['nodes'] == l1) & (r_df['techs'] == t)][results_var]) != 0:
                    if index:
                            values = r_df.loc[(r_df['nodes'] == l1) & (r_df['techs'] == t)][[index,results_var]]
                            locations['techs'][t][results_var] = {'data':list(values[results_var]),'index':list(values[index]),'dims':[index]}
                    else:
                        locations['techs'][t][results_var] = float(r_df.loc[(r_df['nodes'] == l1) &
                                                                    (r_df['techs'] == t)][results_var].values[0])
    yaml.dump(model, open(os.path.join(operate_dir,'model.yaml'),'w+'), default_flow_style=False)
    yaml.dump(techs, open(os.path.join(operate_dir,'techs.yaml'),'w+'), default_flow_style=False)
    yaml.dump(locations, open(os.path.join(operate_dir,'locations.yaml'),'w+'), default_flow_style=False)

def apply_gradient(old_inputs,old_results,new_inputs,old_year,new_year,old_operate_inputs,new_operate_inputs, logger):
    old_model = yaml.safe_load(open(old_results+'/model_results.yaml'))

    new_techs = yaml.safe_load(open(new_inputs+'/techs.yaml','r'))
    new_loctechs = yaml.safe_load(open(new_inputs+'/locations.yaml','r'))
    new_model = yaml.safe_load(open(new_inputs+'/model.yaml','r'))
    new_constraints = yaml.safe_load(open(new_inputs+'/custom_math.yaml'))

    if new_operate_inputs and old_operate_inputs:
        new_operate_techs = yaml.safe_load(open(new_operate_inputs+'/techs.yaml','r'))
        new_operate_loctechs = yaml.safe_load(open(new_operate_inputs+'/locations.yaml','r'))
        new_operate_model = yaml.safe_load(open(new_operate_inputs+'/model.yaml','r'))
        new_operate_constraints = yaml.safe_load(open(new_operate_inputs+'/custom_math.yaml'))

        old_operate_techs = yaml.safe_load(open(old_operate_inputs+'/techs.yaml','r'))
        old_operate_loctechs = yaml.safe_load(open(old_operate_inputs+'/locations.yaml','r'))
        old_operate_model = yaml.safe_load(open(old_operate_inputs+'/model.yaml','r'))

    built_techs = {'techs':{},'templates':{}}
    built_loc_techs = {}

    zero_param = {'data':[0]}

    for l in old_model['nodes']:
        if 'techs' in old_model['nodes'][l] and old_model['nodes'][l]['techs']:
            for t in old_model['nodes'][l]['techs']:
                old_tech = old_model['techs'][t]
                if t not in new_techs['techs']:
                    continue
                new_tech = new_techs['techs'][t]
                new_loc_tech = new_loctechs['nodes'][l]['techs'][t]
                loc_tech = old_model['nodes'][l]['techs'][t]
                max_params = {'flow_cap':'flow_cap_max','storage_cap':'storage_cap_max','purchased_units':'purchased_units_max'}
                min_params = {'flow_cap':'flow_cap_min','storage_cap':'storage_cap_min','purchased_units':'purchased_units_min'}
                if any([x in loc_tech or x in old_tech for x in max_params.values()]):
                    # A capex tech will have a min less than max rather than equal. All fixed techs can be ignored
                    capex_params = {}
                    for param in max_params.keys():
                        param_max = loc_tech.get(max_params[param],old_tech.get(max_params[param], None))
                        param_min = loc_tech.get(min_params[param],old_tech.get(min_params[param], None))
                        param_result = loc_tech.get('results',{param:False}).get(param,False)
                        if not param_result:
                            continue
                        elif not param_min or not param_max:
                                capex_params[param] = param_result
                        elif isinstance(param_max, dict) and 'data' in param_max:
                            if sum(param_max['data']) > sum(param_min['data']):
                                capex_params[param] = param_result
                        else:
                            if param_max > param_min:
                                capex_params[param] = param_result

                    for param, param_result in capex_params.items():
                        if isinstance(param_result, dict) and 'data' in param_result:
                            built_capacities = dict(zip(param_result['index'],param_result['data']))
                        else:
                            built_capacities = {param_result:0}
                        # Unbuilt techs will have 0 capacity in results and can be skipped
                        if sum(built_capacities.values()) != 0:
                            loc_tech_b = copy.deepcopy(loc_tech)

                            # Record built techs and the total systemwide capacity of those techs to use with flow_cap_max_systemwide
                            if t not in built_techs['techs']:
                                built_techs['techs'][t] = {}
                            if param not in built_techs['techs'][t]:
                                built_techs['techs'][t][param] = {}
                            
                            for index, value in built_capacities.items():
                                if index not in built_techs['techs'][t]:
                                    built_techs['techs'][t][param][index] = value
                                else:
                                    built_techs['techs'][t][param][index] += value
                            
                            [loc_tech_b.pop(c) for c in [max_params[param], min_params[param]] if c in loc_tech_b]
                            if param in loc_tech['results']:
                                loc_tech_b[max_params[param]] = loc_tech['results'][param]
                                loc_tech_b[min_params[param]] = loc_tech['results'][param]
                            [loc_tech_b.pop(c) for c in ['cost_flow_cap','cost_interest_rate','cost_storage_cap'] if c in loc_tech_b]
                            loc_tech_b.pop('results')
                            minmax_params = {max_params[param]: param, min_params[param]: param}
                            for param, result in minmax_params.items():
                                if new_loc_tech:
                                    new_param = new_loc_tech.get(param,new_tech.get(param,None))
                                else:
                                    new_param = new_tech.get(param,None)
                                if new_loc_tech is None:
                                    new_loc_tech = {}

                                if new_param:
                                    if isinstance(new_param, dict) and 'data' in new_param:
                                        new_param_dims = new_param['dims']
                                        new_param_values = dict(zip(new_param['index'],new_param['data']))
                                        for index, value in new_param_values.items():
                                            new_param_values[index] -= built_capacities.get(index, 0)
                                        new_loc_tech[param] = {'data':[x if x >= 0 else 0 for x in new_param_values.values()],'index':list(new_param_values.keys()),'dims':new_param_dims}
                                    elif param in loc_tech['results']:
                                        new_loc_tech[param] = max([new_param-loc_tech['results'][result],0])
                            new_loctechs['nodes'][l]['techs'][t] = new_loc_tech

                            built_loc_techs[l+t] = loc_tech_b

                            new_loctechs['nodes'][l]['techs'][t+'_'+str(old_year)] = loc_tech_b

                            if old_operate_inputs and new_operate_inputs:
                                new_operate_loctechs['nodes'][l]['techs'][t+'_'+str(old_year)] = copy.deepcopy(old_operate_loctechs['nodes'][l]['techs'][t])

    # Transmission (formerly links)
    for l in old_model['techs']:
        if 'link_from' not in old_model['techs'][l] or 'link_to' not in old_model['techs'][l]:
            continue
        t = old_model['techs'][l]['template']
        old_tech = old_model['templates'][t]
        if t not in new_techs['templates']:
            continue
        new_tech = new_techs['templates'][t]
        new_loc_tech = new_loctechs['techs'][l]
        loc_tech = old_model['techs'][l]
        # Check if tech has a max flow or storage capacity
        max_params = {'flow_cap':'flow_cap_max','storage_cap':'storage_cap_max','purchased_units':'purchased_units_max'}
        min_params = {'flow_cap':'flow_cap_min','storage_cap':'storage_cap_min','purchased_units':'purchased_units_min'}
        if any([x in loc_tech or x in old_tech for x in max_params.values()]):
            # A capex tech will have a min less than max rather than equal. All fixed techs can be ignored
            capex_params = {}
            for param in max_params.keys():
                param_max = loc_tech.get(max_params[param],old_tech.get(max_params[param], None))
                param_min = loc_tech.get(min_params[param],old_tech.get(min_params[param], None))
                param_result = loc_tech.get('results',{param:False}).get(param,False)
                if not param_result:
                    continue
                elif not param_min or not param_max:
                        capex_params[param] = param_result
                elif isinstance(param_max, dict) and 'data' in param_max:
                    if sum(param_max['data']) > sum(param_min['data']):
                        capex_params[param] = param_result
                else:
                    if param_max > param_min:
                        capex_params[param] = param_result
            
            # A capex tech will have a min less than max rather than equal. All fixed techs can be ignored
            for param, param_result in capex_params.items():
                if isinstance(param_result, dict) and 'data' in param_result:
                    built_capacities = dict(zip(param_result['index'],param_result['data']))
                else:
                    built_capacities = {param_result:0}
                # Unbuilt techs will have 0 capacity in results and can be skipped
                if sum(built_capacities.values()) != 0:
                    loc_tech_b = copy.deepcopy(loc_tech)

                    # Record built techs and the total systemwide capacity of those techs to use with flow_cap_max_systemwide
                    if t not in built_techs['templates']:
                        built_techs['templates'][t] = {}
                    if param not in built_techs['templates'][t]:
                        built_techs['templates'][t][param] = {}
                    
                    for index, value in built_capacities.items():
                        if index not in built_techs['templates'][t]:
                            built_techs['templates'][t][param][index] = value
                        else:
                            built_techs['templates'][t][param][index] += value
                    
                    [loc_tech_b.pop(c) for c in [max_params[param], min_params[param]] if c in loc_tech_b]
                    if param in loc_tech['results']:
                        loc_tech_b[max_params[param]] = loc_tech['results'][param]
                        loc_tech_b[min_params[param]] = loc_tech['results'][param]
                    [loc_tech_b.pop(c) for c in ['cost_flow_cap','cost_interest_rate','cost_storage_cap'] if c in loc_tech_b]
                    loc_tech_b.pop('results')
                    minmax_params = {max_params[param]: param, min_params[param]: param}
                    for param, result in minmax_params.items():
                        if new_loc_tech:
                            new_param = new_loc_tech.get(param,new_tech.get(param,None))
                        else:
                            new_param = new_tech.get(param,None)
                        if new_loc_tech is None:
                            new_loc_tech = {}

                        if new_param:
                            if isinstance(new_param, dict) and 'data' in new_param:
                                new_param_dims = new_param['dims']
                                new_param_values = dict(zip(new_param['index'],new_param['data']))
                                for index, value in new_param_values.items():
                                    new_param_values[index] -= built_capacities.get(index, 0)
                                new_loc_tech[param] = {'data':[x if x >= 0 else 0 for x in new_param_values.values()],'index':list(new_param_values.keys()),'dims':new_param_dims}
                            elif param in loc_tech['results']:
                                new_loc_tech[param] = max([new_param-loc_tech['results'][result],0])

                    new_loctechs['techs'][l] = new_loc_tech

                    built_loc_techs[l+t] = loc_tech_b

                    loc_tech_b['template'] += '_'+str(old_year)

                    new_loctechs['techs'][l+'_'+str(old_year)] = loc_tech_b

                    if old_operate_inputs and new_operate_inputs:
                        new_operate_loctechs['techs'][l+'_'+str(old_year)] = old_operate_loctechs['techs'][l]


    for level in built_techs.keys():
        for t in built_techs[level].keys():
            for param in built_techs[level][t].keys():
                tech = old_model[level][t]
                tech_b = copy.deepcopy(tech)

                # Handle systemwide energy cap gradient
                if f'{param}_max_systemwide' in new_techs[level][t]:
                    new_techs[level][t][f'{param}_max_systemwide'] = max([new_techs[level][t][f'{param}_max_systemwide']-built_techs[level][t],0])
                
                if f'{param}_max' in tech_b:
                    tech_b.pop(f'{param}_max')
                #[tech_b.pop(c) for c in ['cost_flow_cap','cost_interest_rate','cost_storage_cap'] if c in tech_b]
                
                tech_b['name'] += ' '+str(old_year)

                new_techs[level][t+'_'+str(old_year)] = tech_b

                if new_constraints['constraints']:
                    group_constraints = new_constraints['constraints'].copy()
                    for g,c in group_constraints.items():
                        for s,sc in c.get('slices',{}).items():
                            for i,se in enumerate(sc):
                                if t in se['expression'] and t+'_'+str(old_year) not in se['expression']:
                                    new_constraints['constraints'][g]['slices'][s][i]['expression'] = se['expression'].replace(t,t+','+t+'_'+str(old_year))

                if old_operate_inputs and new_operate_inputs:
                    new_operate_techs[level][t+'_'+str(old_year)] = old_operate_techs[level][t]
                    new_operate_techs[level][t+'_'+str(old_year)]['name'] += ' '+str(old_year)
                    if new_operate_constraints['constraints']:
                        operate_group_constraints = new_operate_constraints['constraints'].copy()
                        for g,c in operate_group_constraints.items():
                            for s,sc in c.get('slices',{}).items():
                                for i,se in enumerate(sc):
                                    if t in se['expression'] and t+'_'+str(old_year) not in se['expression']:
                                        new_operate_constraints['constraints'][g]['slices'][s][i]['expression'] = se['expression'].replace(t,t+','+t+'_'+str(old_year))

    for key, ts_file in old_model.get('data_tables',{}).items():
        num_keys = len(ts_file['columns'])
        ts_index = tuple(['ts']*num_keys)
        ts_df_old = pd.read_csv(os.path.join(old_inputs,ts_file['data']),header=list(range(0, num_keys)),index_col=[0])
        node_col = ts_file['columns'].index('nodes') if 'nodes' in ts_file['columns'] else None
        tech_col = ts_file['columns'].index('techs') if 'techs' in ts_file['columns'] else None
        if node_col is not None and tech_col is not None:
            keep_cols = [c[tech_col]+c[node_col] in built_loc_techs for c in ts_df_old.columns]
        elif tech_col is not None:
            keep_cols = [(c[tech_col] in built_techs.get('techs',{}) or c[tech_col] in built_techs.get('templates',{})) for c in ts_df_old.columns]
        ts_df_old.columns = pd.MultiIndex.from_tuples([tuple([c[x]+f'_{str(old_year)}' if x == tech_col else c[x] for x in range(0,num_keys)]) for c in ts_df_old.columns])
        ts_df_old = ts_df_old.loc[:,keep_cols]
        if ts_df_old.empty:
            continue
        ts_df_old[ts_index] = pd.to_datetime(ts_df_old.index)
        if not calendar.isleap(new_year):
            feb_29_mask = (ts_df_old[ts_index].dt.month == 2) & (ts_df_old[ts_index].dt.day == 29)
            ts_df_old = ts_df_old[~feb_29_mask]
            ts_df_old.index = ts_df_old[ts_index].apply(lambda x: x.replace(year=new_year))
        elif not calendar.isleap(old_year):
            ts_df_old.index = ts_df_old[ts_index].apply(lambda x: x.replace(year=new_year))

            # Leap Year Handling (Fill w/ Feb 28th)
            feb_28_mask = (ts_df_old.index.month == 2) & (ts_df_old.index.day == 28)
            feb_29_mask = (ts_df_old.index.month == 2) & (ts_df_old.index.day == 29)
            feb_28 = ts_df_old.loc[feb_28_mask].values
            feb_29 = ts_df_old.loc[feb_29_mask].values
            if ((len(feb_29) > 0) & (len(feb_28) > 0)):
                ts_df_old.loc[feb_29_mask] = feb_28

        ts_df_old.drop(columns=[ts_index],inplace=True)

        if os.path.exists(os.path.join(new_inputs,ts_file['data'])):
            ts_df_new = pd.read_csv(os.path.join(new_inputs,ts_file['data']),header=list(range(0, num_keys)),index_col=[0])
            ts_df_new.index = pd.to_datetime(ts_df_new.index)
            ts_df_new = pd.concat([ts_df_new,ts_df_old],axis=1)
        else:
            new_model['data_sources'][key] = {'source': ts_file['data'], 'rows': 'timesteps',
                                                                'columns': ts_file['columns']}
            ts_df_new = ts_df_old
        ts_df_new.index.name = None
        ts_df_new.to_csv(os.path.join(new_inputs,ts_file['data']))


    with open(new_inputs+'/techs.yaml','w') as outfile:
        yaml.dump(new_techs,outfile, default_flow_style=None)

    with open(new_inputs+'/locations.yaml','w') as outfile:
        yaml.dump(new_loctechs,outfile,default_flow_style=None)

    with open(new_inputs+'/model.yaml', 'w') as outfile:
        yaml.dump(new_model,outfile,default_flow_style=None)

    with open(new_inputs+'/custom_math.yaml', 'w') as outfile:
        yaml.dump(new_constraints,outfile,default_flow_style=None)

    if new_operate_inputs and old_operate_inputs:
        for key, ts_file in old_operate_model.get('data_tables',{}).items():
            num_keys = len(ts_file['columns'])
            ts_index = tuple(['ts']*num_keys)
            ts_df_old = pd.read_csv(os.path.join(old_inputs,ts_file['data']),header=list(range(0, num_keys)),index_col=[0])
            node_col = ts_file['columns'].index('nodes') if 'nodes' in ts_file['columns'] else None
            tech_col = ts_file['columns'].index('techs') if 'techs' in ts_file['columns'] else None
            if node_col is not None and tech_col is not None:
                keep_cols = [c[tech_col]+c[node_col] in built_loc_techs for c in ts_df_old.columns]
            elif tech_col is not None:
                keep_cols = [(c[tech_col] in built_techs.get('techs',{}) or c[tech_col] in built_techs.get('templates',{})) for c in ts_df_old.columns]
            ts_df_old.columns = pd.MultiIndex.from_tuples([tuple([c[x]+f'_{str(old_year)}' if x == tech_col else c[x] for x in range(0,num_keys)]) for c in ts_df_old.columns])
            ts_df_old = ts_df_old.loc[:,keep_cols]
            if ts_df_old.empty:
                continue
            ts_df_old[ts_index] = pd.to_datetime(ts_df_old.index)
            if not calendar.isleap(new_year):
                feb_29_mask = (ts_df_old[ts_index].dt.month == 2) & (ts_df_old[ts_index].dt.day == 29)
                ts_df_old = ts_df_old[~feb_29_mask]
                ts_df_old.index = ts_df_old[ts_index].apply(lambda x: x.replace(year=new_year))
            elif not calendar.isleap(old_year):
                ts_df_old.index = ts_df_old[ts_index].apply(lambda x: x.replace(year=new_year))

                # Leap Year Handling (Fill w/ Feb 28th)
                feb_28_mask = (ts_df_old.index.month == 2) & (ts_df_old.index.day == 28)
                feb_29_mask = (ts_df_old.index.month == 2) & (ts_df_old.index.day == 29)
                feb_28 = ts_df_old.loc[feb_28_mask].values
                feb_29 = ts_df_old.loc[feb_29_mask].values
                if ((len(feb_29) > 0) & (len(feb_28) > 0)):
                    ts_df_old.loc[feb_29_mask] = feb_28

            ts_df_old.drop(columns=[ts_index],inplace=True)

            if os.path.exists(os.path.join(new_operate_inputs,ts_file['data'])):
                ts_df_new = pd.read_csv(os.path.join(new_inputs,ts_file['data']),header=list(range(0, num_keys)),index_col=[0])
                ts_df_new.index = pd.to_datetime(ts_df_new.index)
                ts_df_new = pd.concat([ts_df_new,ts_df_old],axis=1)
            else:
                new_model['data_sources'][key] = {'source': ts_file['data'], 'rows': 'timesteps',
                                                                    'columns': ts_file['columns']}
                ts_df_new = ts_df_old
            ts_df_new.index.name = None
            ts_df_new.to_csv(os.path.join(new_operate_inputs,ts_file['data']))


        with open(new_operate_inputs+'/techs.yaml','w') as outfile:
            yaml.dump(new_operate_techs,outfile, default_flow_style=None)

        with open(new_operate_inputs+'/locations.yaml','w') as outfile:
            yaml.dump(new_operate_loctechs,outfile,default_flow_style=None)

        with open(new_operate_inputs+'/model.yaml', 'w') as outfile:
            yaml.dump(new_operate_model,outfile,default_flow_style=None)

        with open(new_operate_inputs+'/custom_math.yaml', 'w') as outfile:
            yaml.dump(new_operate_constraints,outfile,default_flow_style=None)
