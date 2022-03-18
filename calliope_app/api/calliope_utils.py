"""
This module contains support functions and libraries used in
interfacing with Calliope.
"""

import os
import yaml
import shutil
from calliope import Model as CalliopeModel
import pandas as pd

from api.models.configuration import Scenario_Param, Scenario_Loc_Tech, \
    Location, Tech_Param, Loc_Tech_Param, Loc_Tech


def get_model_yaml_set(scenario_id, year):
    """ Function pulls model parameters from Database for YAML """
    params = Scenario_Param.objects.filter(scenario_id=scenario_id,
                                           year__lte=year).order_by('-year')
    # Initialize the Return list
    model_yaml_set = []
    # There are no timeseries in Run Parameters
    is_timeseries = False
    # Tracks which parameters have already been set (prioritized by year)
    unique_params = []
    # Loop over Parameters
    for param in params:
        unique_param = param.run_parameter.root+param.run_parameter.name

        # NOTE: deprecated run parameter in the database
        if unique_param == "runobjective_options":
            continue
        
        if unique_param not in unique_params:
            # If parameter hasn't been set, add to Return List
            unique_params.append(unique_param)
            if "." in param.run_parameter.root:
                items = param.run_parameter.root.split(".")
                param_list = items + [param.run_parameter.name, param.value]
            else:
                param_list = [
                    param.run_parameter.root,
                    param.run_parameter.name,
                    param.value
                ]
            model_yaml_set.append((stringify(param_list), is_timeseries))
    model_yaml_set += [('import||["techs.yaml","locations.yaml"]', False)]
    return model_yaml_set


def get_location_meta_yaml_set(scenario_id):
    """ Function pulls model locations from Database for YAML """
    loc_techs = Scenario_Loc_Tech.objects.filter(scenario_id=scenario_id)
    loc_ids = loc_techs.values_list('loc_tech__location_1',
                                    'loc_tech__location_2')
    loc_ids = list(filter(None, set(
        [item for sublist in loc_ids for item in sublist])))
    locations = Location.objects.filter(id__in=loc_ids)
    # Initialize the Return list
    location_coord_yaml_set = []
    # There are no timeseries in Location Coordinates
    is_timeseries = False
    # Loop over Parameters
    for loc in locations:
        # Coordinates
        coordinates = '{{"lat": {}, "lon": {}}}'.format(loc.latitude,
                                                        loc.longitude)
        param_list = ['locations', loc.name, 'coordinates', coordinates]
        location_coord_yaml_set.append((stringify(param_list), is_timeseries))
        # Available Area
        if loc.available_area is None:
            continue
        param_list = ['locations', loc.name,
                      'available_area', loc.available_area]
        location_coord_yaml_set.append((stringify(param_list), is_timeseries))
    return location_coord_yaml_set


def get_techs_yaml_set(scenario_id, year):
    """ Function pulls tech parameters from Database for YAML """
    loc_techs = Scenario_Loc_Tech.objects.filter(scenario_id=scenario_id)
    tech_ids = list(loc_techs.values_list('loc_tech__technology',
                                          flat=True).distinct())
    parameters = Tech_Param.objects.filter(technology_id__in=tech_ids,
                                           year__lte=year).order_by('-year')
    # Initialize the Return list
    techs_yaml_set = []
    # Loop over Technologies
    for tech_id in tech_ids:
        params = parameters.filter(technology_id=tech_id)
        # Tracks which parameters have already been set (prioritized by year)
        unique_params = []
        # Loop over Parameters
        for param in params:
            unique_param = param.parameter.root + param.parameter.name
            if unique_param not in unique_params:
                # If parameter hasn't been set, add to Return List
                unique_params.append(unique_param)
                is_timeseries = param.timeseries
                if '%' in param.parameter.units:  # Calliope in decimal format
                    value = float(param.value) / 100
                else:
                    value = param.value
                param_list = ['techs', param.technology.calliope_name,
                              param.parameter.root, param.parameter.name,
                              value]
                techs_yaml_set.append((stringify(param_list), is_timeseries))
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
    loc_techs_yaml_set = []
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

        if len(params) == 0:
            is_timeseries = False
            param_list = [parent_type, location, 'techs',
                          loc_tech.technology.calliope_name, '']
            loc_techs_yaml_set.append((stringify(param_list), is_timeseries))
            continue

        # Tracks which parameters have already been set (prioritized by year)
        unique_params = []
        # Loop over Parameters
        for param in params:
            unique_param = param.parameter.root + param.parameter.name
            if unique_param not in unique_params:
                # If parameter hasn't been set, add to Return List
                unique_params.append(unique_param)
                is_timeseries = param.timeseries
                if '%' in param.parameter.units:  # Calliope in decimal format
                    value = float(param.value) / 100
                else:
                    value = param.value
                param_list = [parent_type, location, 'techs',
                              param.loc_tech.technology.calliope_name,
                              param.parameter.root,
                              param.parameter.name,
                              value]
                loc_techs_yaml_set.append((stringify(param_list),
                                           is_timeseries))
    return loc_techs_yaml_set


def stringify(param_list):
    param_list = [str(x) for x in param_list]
    return '||'.join(param_list).replace('||||', '||')


def run_basic(model_path, logger):
    """ Basic Run """
    logger.info('--- Run Basic')
    model = CalliopeModel(config=model_path)
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
        _yaml_outputs(model,model_path,final_outputs)
    else:
        _yaml_outputs(model,model_path,save_outputs)

def _yaml_outputs(model, model_path, outputs_dir):
    base_path = os.path.dirname(os.path.dirname(model_path))
    results_var = {'energy_cap':'results_energy_cap.csv'}
    inputs_dir = os.path.join(base_path, 'inputs')

    model = yaml.load(open(os.path.join(inputs_dir,'model.yaml')), Loader=yaml.FullLoader)
    model.update(yaml.load(open(os.path.join(inputs_dir,'locations.yaml')), Loader=yaml.FullLoader))
    model.update(yaml.load(open(os.path.join(inputs_dir,'techs.yaml')), Loader=yaml.FullLoader))

    for v in results_var.keys():
        r_df = pd.read_csv(os.path.join(outputs_dir,results_var[v]))

        for tl in ['locations','links']:
            for l in model[tl].keys():
                if tl == 'links':
                    l1 = l.split(',')[0]
                    l2 = l.split(',')[1]
                if 'techs' in model[tl][l].keys():
                    for t in model[tl][l]['techs'].keys():
                        if model[tl][l]['techs'][t] == None:
                            model[tl][l]['techs'][t] = {}
                        model[tl][l]['techs'][t]['results'] = {}
                        if tl == 'links':
                            model[tl][l]['techs'][t]['results']['energy_cap'] = float(r_df.loc[(r_df['locs'] == l1) &
                                                                                (r_df['techs'] == t+':'+l2)]['energy_cap'].values[0])
                        else:
                            model[tl][l]['techs'][t]['results']['energy_cap'] = float(r_df.loc[(r_df['locs'] == l) &
                                                                                (r_df['techs'] == t)]['energy_cap'].values[0])

    yaml.dump(model, open(os.path.join(outputs_dir,'model_results.yaml'),'w+'), default_flow_style=False)