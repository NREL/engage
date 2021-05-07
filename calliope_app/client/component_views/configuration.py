from django.conf import settings
from django.http import HttpResponse, JsonResponse
from django.shortcuts import render
from django.views.decorators.csrf import csrf_protect
from django.utils.timezone import make_aware

from api.models.configuration import Scenario_Param, Scenario_Loc_Tech, \
    Timeseries_Meta, ParamsManager, Model, User_File
from api.utils import get_cols_from_csv

import os
import json
from datetime import datetime, timedelta
import string
import pandas as pd


@csrf_protect
def location_coordinates(request):
    """
    Retrieve the coordinates of locations in model

    Parameters:
    model_uuid (uuid): required
    scenario_id (int): optional
    technology_id (int): optional
    loc_tech_id (int): optional

    Returns: JsonResponse

    Example:
    GET: /component/location_coordinates/
    """

    model_uuid = request.GET['model_uuid']
    scenario_id = request.GET.get('scenario_id', None)
    technology_id = request.GET.get('technology_id', None)
    loc_tech_id = request.GET.get('loc_tech_id', None)

    model = Model.by_uuid(model_uuid)
    model.handle_view_access(request.user)

    locations = list(model.locations.values())

    # Get Locations included in Scenario
    scenario_loc_techs = Scenario_Loc_Tech.objects.filter(
        scenario_id=scenario_id)
    selected_ids = []
    transmissions = []
    for slt in scenario_loc_techs:
        selected_ids.append(slt.loc_tech.location_1_id)
        selected_ids.append(slt.loc_tech.location_2_id)
        if slt.loc_tech.location_2_id:
            trans = {
                'id': slt.loc_tech_id,
                'name': slt.loc_tech.technology.pretty_name,
                'lat1': slt.loc_tech.location_1.latitude,
                'lon1': slt.loc_tech.location_1.longitude,
                'lat2': slt.loc_tech.location_2.latitude,
                'lon2': slt.loc_tech.location_2.longitude,
            }
            transmissions.append(trans)

    # Get unselected Location Technologies
    unselected_ids = []
    loc_techs = model.loc_techs.filter(technology_id=technology_id)
    for lt in loc_techs:
        unselected_ids.append(lt.location_1_id)

    # Get selected Location Technology
    loc_tech = model.loc_techs.filter(id=loc_tech_id).first()
    if loc_tech:
        selected_ids.append(loc_tech.location_1_id)
        selected_ids.append(loc_tech.location_2_id)

    selected_ids = list(set(selected_ids))

    # Set Location View Type
    for i in range(len(locations)):
        if locations[i]['id'] in selected_ids:
            locations[i]['type'] = 'selected'
        elif locations[i]['id'] in unselected_ids:
            locations[i]['type'] = 'unselected'
        else:
            locations[i]['type'] = 'reference'
    locations = sorted(locations, key=lambda k: k['type'])

    response = {
        'locations': locations,
        'transmissions': transmissions,
    }
    return JsonResponse(response, safe=False)


@csrf_protect
def all_tech_params(request):
    """
    Retrieve the parameters for a technology

    Parameters:
    model_uuid (uuid): required
    technology_id (int): required

    Returns: HttpResponse

    Example:
    GET: /component/all_tech_params/
    """

    model_uuid = request.GET['model_uuid']
    technology_id = request.GET['technology_id']
    request.session['technology_id'] = technology_id

    model = Model.by_uuid(model_uuid)
    can_edit = model.handle_view_access(request.user)

    technology = model.technologies.get(id=technology_id)
    essentials, parameters = ParamsManager.all_tech_params(technology)
    timeseries = Timeseries_Meta.objects.filter(model=model, failure=False,
                                                is_uploading=False)

    # Technology Definition
    context = {"technology": technology,
               "essentials": essentials,
               "carriers": model.carriers,
               "required_carrier_ids": [4, 5, 6],
               "cplus_carrier_ids": [66, 67, 68, 69],
               "can_edit": can_edit}
    html_essentials = list(render(request,
                                  'technology_essentials.html',
                                  context))[0]

    # Parameters Table
    context = {
        "technology": technology,
        "model": model,
        "parameters": parameters,
        "carriers": model.carriers,
        "level": "1_tech",
        "timeseries": timeseries,
        "can_edit": can_edit}
    html_parameters = list(render(request,
                                  'technology_parameters.html',
                                  context))[0]

    payload = {
        'technology_id': technology_id,
        'html_essentials': html_essentials.decode('utf-8'),
        'html_parameters': html_parameters.decode('utf-8'),
        'favorites': model.favorites}

    return HttpResponse(json.dumps(payload), content_type="application/json")


@csrf_protect
def all_loc_techs(request):
    """
    Retrieve the nodes for a technology

    Parameters:
    model_uuid (uuid): required
    technology_id (int): required

    Returns: HttpResponse

    Example:
    GET: /component/all_loc_techs/
    """

    model_uuid = request.GET['model_uuid']
    technology_id = int(request.GET['technology_id'])
    request.session['technology_id'] = technology_id

    session_loc_tech_id = request.session.get('loc_tech_id', None)

    model = Model.by_uuid(model_uuid)
    can_edit = model.handle_view_access(request.user)

    technology = model.technologies.filter(id=technology_id).first()
    loc_techs = model.loc_techs.filter(technology_id=technology_id)

    context = {
        "model": model,
        "locations": model.locations,
        "technology": technology,
        "loc_techs": loc_techs,
        "session_loc_tech_id": session_loc_tech_id,
        "can_edit": can_edit}
    html_essentials = list(render(request,
                                  'loc_tech_essentials.html',
                                  context))[0]

    payload = {
        'technology_id': technology_id,
        'html_essentials': html_essentials.decode('utf-8'),
        'loc_techs': list(loc_techs.values())
    }

    return JsonResponse(payload)


@csrf_protect
def all_loc_tech_params(request):
    """
    Retrieve the parameters for a node

    Parameters:
    model_uuid (uuid): required
    loc_tech_id (int): required

    Returns: HttpResponse

    Example:
    GET: /component/all_loc_tech_params/
    """

    model_uuid = request.GET['model_uuid']
    loc_tech_id = int(request.GET['loc_tech_id'])
    request.session['loc_tech_id'] = loc_tech_id

    model = Model.by_uuid(model_uuid)
    can_edit = model.handle_view_access(request.user)

    loc_tech = model.loc_techs.get(id=loc_tech_id)
    parameters = ParamsManager.all_loc_tech_params(loc_tech)
    timeseries = Timeseries_Meta.objects.filter(model=model, failure=False,
                                                is_uploading=False)

    # Parameters Table
    context = {
        "loc_tech": loc_tech,
        "model": model,
        "parameters": parameters,
        "carriers": model.carriers,
        "level": "2_loc_tech",
        "timeseries": timeseries,
        "can_edit": can_edit}
    html_parameters = list(render(request,
                                  'technology_parameters.html',
                                  context))[0]

    payload = {
        'loc_tech_id': loc_tech_id,
        'html_parameters': html_parameters.decode('utf-8'),
        'favorites': model.favorites}

    return HttpResponse(json.dumps(payload), content_type="application/json")


@csrf_protect
def timeseries_view(request):
    """
    Retrieve timeseries data

    Parameters:
    model_uuid (uuid): required
    timeseries_meta_id (int): required
    start_date (timestamp): required
    end_date (timestamp): required

    Returns: JsonResponse

    Example:
    GET: /component/timeseries_view/
    """

    model_uuid = request.GET.get('model_uuid', None)
    timeseries_meta_id = request.GET.get('ts_id', None)
    start_date = request.GET.get('start_date', None)
    end_date = request.GET.get('end_date', None)

    model = Model.by_uuid(model_uuid)
    model.handle_view_access(request.user)

    timeseries_meta = Timeseries_Meta.objects.get(id=timeseries_meta_id)
    timeseries = timeseries_meta.get_timeseries()

    min_date, max_date = timeseries_meta.get_period()

    # Validate start_date, end_date
    if start_date is not None:
        try:
            start_date = make_aware(datetime.strptime(
                start_date.strip()[0:10], '%Y-%m-%d')).replace(tzinfo=None)
        except ValueError:
            start_date = None
    if end_date is not None:
        try:
            end_date = make_aware(datetime.strptime(
                end_date.strip()[0:10], '%Y-%m-%d')).replace(tzinfo=None)
        except ValueError:
            end_date = None

    if start_date is not None and end_date is not None:
        if start_date > end_date:
            temp_date = start_date
            start_date = end_date
            end_date = temp_date

        if end_date - start_date <= timedelta(days=1):
            # add one day
            end_date = start_date + timedelta(days=1)

    if start_date is not None:
        if start_date <= min_date or start_date >= max_date:
            start_date = min_date
        timeseries = timeseries[timeseries.datetime >= start_date]

    if end_date is not None:
        if end_date <= min_date or end_date >= (max_date + timedelta(days=1)):
            end_date = max_date + timedelta(days=1)
        timeseries = timeseries[timeseries.datetime < end_date]

    if len(timeseries) > 8784:  # hours in one year
        # get max value for each day
        timeseries = timeseries.resample('D').max()

    timestamps = timeseries.datetime.dt.strftime(
        '%Y-%m-%d %H:%M:%S').values.tolist()
    values = timeseries.value.values.tolist()

    payload = {
        'timestamps': timestamps,
        'values': values,
    }
    return JsonResponse(payload)


@csrf_protect
def scenario(request):
    """
    Retrieve the parameters and nodes for a scenario

    Parameters:
    model_uuid (uuid): required
    scenario_id (int): required

    Returns: HttpResponse

    Example:
    GET: /component/scenario/
    """

    model_uuid = request.GET['model_uuid']
    scenario_id = request.GET['scenario_id']
    request.session['scenario_id'] = scenario_id

    model = Model.by_uuid(model_uuid)
    can_edit = model.handle_view_access(request.user)

    # Scenario Parameters
    colors = model.color_lookup
    parameters = Scenario_Param.objects.filter(
        model_id=model.id, scenario_id=scenario_id,
        run_parameter__user_visibility=True)

    # All Loc Techs
    loc_techs = []
    lts = model.loc_techs
    lts = lts.values('id', 'technology_id', 'technology__pretty_name',
                     'technology__pretty_tag',
                     'technology__abstract_tech__icon',
                     'location_1__pretty_name', 'location_2__pretty_name')
    for lt in lts:
        tech_id = lt["technology_id"]
        color = colors[tech_id] if tech_id in colors.keys() else "#000"
        loc_techs.append({
            "id": lt['id'],
            "technology_id": lt['technology_id'],
            "tag": lt["technology__pretty_tag"],
            "technology": lt["technology__pretty_name"],
            "location_1": lt["location_1__pretty_name"],
            "location_2": lt["location_2__pretty_name"],
            "color": color,
            "icon": lt["technology__abstract_tech__icon"]})

    # Active Loc Techs
    active_lts = Scenario_Loc_Tech.objects.filter(scenario_id=scenario_id)
    active_lt_ids = list(active_lts.values_list("loc_tech_id", flat=True))

    # Filters Data
    unique_techs = [v['technology'] for v in loc_techs]
    unique_tags = [v['tag'] for v in loc_techs]
    locations = [(v['location_1'],
                  v['location_2']) for v in loc_techs]
    unique_locations = [item for sublist in locations for item in sublist]

    context = {
        "model": model,
        "parameters": parameters,
        "can_edit": can_edit}
    scenario_settings = list(render(request,
                                    'scenario_settings.html',
                                    context))[0]
    context = {
        "model": model,
        "colors": colors,
        "carrier_ins": model.carrier_lookup(True),
        "carrier_outs": model.carrier_lookup(False),
        "active_lt_ids": active_lt_ids,
        "loc_techs": loc_techs,
        "scenario_id": scenario_id,
        "unique_techs": sorted(filter(None, set(unique_techs))),
        "unique_tags": sorted(filter(None, set(unique_tags))),
        "unique_locations": sorted(filter(None, set(unique_locations))),
        "can_edit": can_edit}
    scenario_configuration = list(render(request,
                                         'scenario_configuration.html',
                                         context))[0]

    payload = {
        'model_id': model.id,
        'scenario_id': scenario_id,
        'loc_techs': loc_techs,
        'active_lt_ids': active_lt_ids,
        'scenario_settings': scenario_settings.decode('utf-8'),
        'scenario_configuration': scenario_configuration.decode('utf-8')}

    return HttpResponse(json.dumps(payload, indent=4),
                        content_type="application/json")


@csrf_protect
def timeseries_new(request):
    """
    Retrieve form for building a new timeseries

    Parameters:
    model_uuid (uuid): required
    file_id (int): optional

    Returns: HttpResponse

    Example:
    GET: /component/timeseries_new/
    """

    model_uuid = request.GET['model_uuid']
    file_id = request.GET.get('file_id', None)

    model = Model.by_uuid(model_uuid)
    can_edit = model.handle_view_access(request.user)

    columns = None
    file_record = User_File.objects.filter(model=model, id=file_id).first()
    if file_record:
        filename = file_record.filename
        try:
            columns = get_cols_from_csv(filename)
        except Exception as e:
            print('Doesn\'t exist or could not read columns: ' + filename)
            print(e)

    context = {
        "columns": columns,
        "filename": os.path.basename(filename.name),
        "can_edit": can_edit,
        "letters": map(lambda x: 'Column ' + x,
                       string.ascii_uppercase[0:len(columns)])}
    html = list(render(request, 'timeseries_new.html', context))[0]

    payload = {
        'html': html.decode('utf-8')}

    return HttpResponse(json.dumps(payload), content_type="application/json")


@csrf_protect
def timeseries_content(request):
    """
    Retrieve the meta data for all timeseries

    Parameters:
    model_uuid (uuid): required
    file_id (int): optional

    Returns: HttpResponse

    Example:
    GET: /component/timeseries_content/
    """

    model_uuid = request.GET['model_uuid']
    file_id = request.GET.get('file_id', None)

    model = Model.by_uuid(model_uuid)
    can_edit = model.handle_view_access(request.user)

    file_record = User_File.objects.filter(model=model, id=file_id).first()
    file_data = None
    file_syspath = None
    file_size = None
    if file_record:
        if '.csv' in str(file_record.filename):
            file_syspath = os.path.join(settings.DATA_STORAGE,
                                        str(file_record.filename))
            # optimized to only read first 24 lines of file
            # (instead of whole file and then get first 24 lines)
            file_data = pd.read_csv(
                file_syspath, header=None, nrows=24).to_dict('records')
            file_size = os.path.getsize(file_syspath)

    context = {
        "file_data": file_data,
        "file_size": file_size,
        "can_edit": can_edit,
        "letters": map(lambda x: 'Column ' + x,
                       string.ascii_uppercase[0:len(file_data[0])])}

    html = list(render(request, 'timeseries_content.html', context))[0]

    payload = {
        'html': html.decode('utf-8')}

    return HttpResponse(json.dumps(payload), content_type="application/json")
