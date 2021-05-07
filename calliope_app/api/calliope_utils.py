"""
This module contains support functions and libraries used in
interfacing with Calliope.
"""

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
        unique_param = param.run_parameter.name
        if unique_param not in unique_params:
            # If parameter hasn't been set, add to Return List
            unique_params.append(unique_param)
            param_list = [param.run_parameter.root,
                          param.run_parameter.name,
                          param.value]
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
            unique_param = param.parameter.name
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
            unique_param = param.parameter.name
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
