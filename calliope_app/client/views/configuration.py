import json
from django.conf import settings
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseRedirect
from django.urls import reverse
from django.db.models import Q
from django_ratelimit.decorators import ratelimit
from django.http import JsonResponse
from api.models.engage import Help_Guide
from api.models.calliope import Parameter, Abstract_Tech
from api.models.configuration import Model, User_File, \
    Technology, Loc_Tech, Timeseries_Meta, Model_User, \
    Model_Comment, Carrier, Tech_Param, Loc_Tech_Param
from pytz import common_timezones
import logging
from api.views.configuration import get_map_box_token

logger = logging.getLogger(__name__)


# ------ Model


def model_view(request, model_uuid):
    """
    View the main model "Activity" page

    Parameters:
    model_uuid (uuid): required

    Returns: HttpResponse

    Example:
    http://0.0.0.0:8000/<model_uuid>/
    """

    model = Model.by_uuid(model_uuid)
    try:
        can_edit = model.handle_view_access(request.user)
    except Exception:
        return HttpResponseRedirect(reverse('home'))

    if request.user.is_authenticated:
        # Update last_access
        model_user = Model_User.objects.filter(user=request.user, model=model)
        if len(model_user) > 0:
            mu = model_user.first()
            mu.notifications = 0
            mu.save()

    carriers = [{'name':carrier.name,'rate':carrier.rate_unit,'quantity':carrier.quantity_unit,'description':carrier.description} for carrier in model.carriers.all()]

    comments = Model_Comment.objects.filter(model=model)

    context = {
        "timezones": common_timezones,
        "user": request.user,
        "model": model,
        "carriers": carriers,
        "comments": comments,
        "can_edit": can_edit,
        "help_content": Help_Guide.get_safe_html('model'),
    }

    return render(request, "activity.html", context)


# ------ Locations


def locations_view(request, model_uuid):
    """
    View the "Locations" page

    Parameters:
    model_uuid (uuid): required

    Returns: HttpResponse

    Example:
    http://0.0.0.0:8000/<model_uuid>/locations
    """
    token_response = get_map_box_token(request)
    response = json.loads(token_response.content.decode('utf-8'))
    token = response.get("token") 

    model = Model.by_uuid(model_uuid)
    try:
        can_edit = model.handle_view_access(request.user)
    except Exception:
        return HttpResponseRedirect(reverse('home'))

    locations = model.locations.values()
    location_ids = [loc['id'] for loc in locations]
    lts = Loc_Tech.objects.filter(
        Q(location_1_id__in=location_ids) | Q(location_2_id__in=location_ids))
    lts = lts.values("id", "technology_id", "location_1_id", "location_2_id",
                     "technology__pretty_name", "technology__pretty_tag", "template_id")
    loc_techs = {}
    for lt in lts:
        l1, l2 = lt["location_1_id"], lt["location_2_id"]
        if l1 not in loc_techs.keys():
            loc_techs[l1] = [lt]
        else:
            loc_techs[l1].append(lt)
        if l2 is not None and l2 not in loc_techs.keys():
            loc_techs[l2] = [lt]
        elif l2 is not None:
            loc_techs[l2].append(lt)

    context = {
        "user": request.user,
        "nrel_api_key": settings.NREL_API_KEY,
        "timezones": common_timezones,
        "model": model,
        "locations": locations,
        "loc_techs": loc_techs,
        "mapbox_token": token,
        "can_edit": can_edit,
        "help_content": Help_Guide.get_safe_html('locations'),
    }

    return render(request, "locations.html", context)


# ------ Technologies


def technologies_view(request, model_uuid):
    """
    View the "Technologies" page

    Parameters:
    model_uuid (uuid): required

    Returns: HttpResponse

    Example:
    http://0.0.0.0:8000/<model_uuid>/technologies
    """

    model = Model.by_uuid(model_uuid)
    try:
        can_edit = model.handle_view_access(request.user)
    except Exception:
        return HttpResponseRedirect(reverse('home'))

    technologies = model.technologies.values(
        "id", "pretty_name", "pretty_tag", "abstract_tech__icon", "template_type_id")
    session_technology_id = request.GET.get('tech_id', None)
    if not session_technology_id:
        session_technology_id = request.session.get('technology_id', None)
    if session_technology_id:
        session_technology_id = int(session_technology_id)
    context = {
        "timezones": common_timezones,
        "model": model,
        "technologies": list(technologies),
        "session_technology_id": session_technology_id,
        "can_edit": can_edit,
        "help_content": Help_Guide.get_safe_html('technologies'),
    }

    return render(request, "technologies.html", context)


@login_required
def add_technologies_view(request, model_uuid):
    """
    View the "Add Technology" page

    Parameters:
    model_uuid (uuid): required

    Returns: HttpResponse

    Example:
    http://0.0.0.0:8000/<model_uuid>/add_technologies_view
    """

    model = Model.by_uuid(model_uuid)
    can_edit = model.handle_view_access(request.user)

    public_model_ids = Model.objects.filter(
        snapshot_version=None,
        public=True).values_list('id', flat=True)
    public_techs = Technology.objects.filter(
        model_id__in=public_model_ids)

    context = {
        "timezones": common_timezones,
        "model": model,
        "abstract_techs": Abstract_Tech.objects.all(),
        "public_techs": public_techs,
        "my_techs": model.technologies,
        "can_edit": can_edit,
        "help_content": Help_Guide.get_safe_html('add_technology'),
    }

    return render(request, "add_technology.html", context)


# ------ Location-Technologies (Nodes)


def loc_techs_view(request, model_uuid):
    """
    View the "Nodes" page

    Parameters:
    model_uuid (uuid): required

    Returns: HttpResponse

    Example:
    http://0.0.0.0:8000/<model_uuid>/loc_techs
    """
    token_response = get_map_box_token(request)
    response = json.loads(token_response.content.decode('utf-8'))
    token = response.get("token") 

    model = Model.by_uuid(model_uuid)
    try:
        can_edit = model.handle_view_access(request.user)
    except Exception:
        return HttpResponseRedirect(reverse('home'))

    technologies = model.technologies.values(
        "id", "pretty_name", "pretty_tag", "abstract_tech__icon", "template_type_id")
    session_technology_id = request.GET.get('tech_id', None)
    session_loc_tech_id = request.GET.get('loc_tech_id', None)
    if not session_technology_id:
        session_technology_id = request.session.get('technology_id', None)
    if session_technology_id:
        session_technology_id = int(session_technology_id)
    if session_loc_tech_id:
        request.session['loc_tech_id'] = int(session_loc_tech_id)
    context = {
        "timezones": common_timezones,
        "model": model,
        "technologies": list(technologies),
        "session_technology_id": session_technology_id,
        "can_edit": can_edit,
        "mapbox_token": token,
        "help_content": Help_Guide.get_safe_html('nodes'),
    }

    return render(request, "loc_techs.html", context)


# ------ Scenarios


def scenarios_view(request, model_uuid):
    """
    View the "Scenarios" page

    Parameters:
    model_uuid (uuid): required

    Returns: HttpResponse

    Example:
    http://0.0.0.0:8000/<model_uuid>/scenarios
    """
    token_response = get_map_box_token(request)
    response = json.loads(token_response.content.decode('utf-8'))
    token = response.get("token") 

    model = Model.by_uuid(model_uuid)
    try:
        can_edit = model.handle_view_access(request.user)
    except Exception:
        return HttpResponseRedirect(reverse('home'))

    scenarios = model.scenarios

    session_scenario_id = request.session.get('scenario_id', None)
    session_scenario = scenarios.filter(id=session_scenario_id).first()

    context = {
        "user": request.user,
        "timezones": common_timezones,
        "model": model,
        "scenarios": scenarios,
        "session_scenario": session_scenario,
        "mapbox_token": token,
        "can_edit": can_edit,
        "help_content": Help_Guide.get_safe_html('scenarios'),
    }

    return render(request, "scenarios.html", context)


@login_required
def add_scenarios_view(request, model_uuid):
    """
    View the "Add Scenario" page

    Parameters:
    model_uuid (uuid): required

    Returns: HttpResponse

    Example:
    http://0.0.0.0:8000/<model_uuid>/add_scenarios_view
    """

    model = Model.by_uuid(model_uuid)
    can_edit = model.handle_view_access(request.user)

    context = {
        "timezones": common_timezones,
        "model": model,
        "scenarios": model.scenarios,
        "can_edit": can_edit,
        "help_content": Help_Guide.get_safe_html('add_scenario'),
    }

    return render(request, "add_scenario.html", context)


# ------ Timeseries


@login_required
def timeseries_view(request, model_uuid):
    """
    View the "Timeseries" page

    Parameters:
    model_uuid (uuid): required

    Returns: HttpResponse

    Example:
    http://0.0.0.0:8000/<model_uuid>/timeseries/
    """

    model = Model.by_uuid(model_uuid)
    can_edit = model.handle_view_access(request.user)

    files = User_File.objects.filter(model=model, filename__contains=".csv")

    context = {
        "timezones": common_timezones,
        "model": model,
        "files": files,
        "can_edit": can_edit,
        "help_content": Help_Guide.get_safe_html('timeseries'),
    }

    return render(request, "timeseries.html", context)


@login_required
def timeseries_table(request, model_uuid):
    """
    View the "Timeseries" page

    Parameters:
    model_uuid (uuid): required

    Returns: HttpResponse

    Example:
    http://0.0.0.0:8000/<model_uuid>/timeseries_table/
    """

    model = Model.by_uuid(model_uuid)
    can_edit = model.handle_view_access(request.user)
    timeseries = Timeseries_Meta.objects.filter(model=model)

    context = {
        "timezones": common_timezones,
        "model": model,
        "timeseries": timeseries,
        "can_edit": can_edit,
    }

    return render(request, "timeseries_table.html", context)


@login_required
def parameters_view(request, model_uuid, parameter_name):
    """
    View the "Parameters" page

    Parameters:
    model_uuid (uuid): required
    parameter_name (str): required

    Returns: HttpResponse

    Example:
    http://0.0.0.0:8000/<model_uuid>/parameters/resource/
    """

    model = Model.by_uuid(model_uuid)
    can_edit = model.handle_view_access(request.user)

    parameter = Parameter.objects.filter(name=parameter_name).first()

    context = {
        "timezones": common_timezones,
        "model": model,
        "parameter": parameter,
        "can_edit": can_edit,
        "help_content": Help_Guide.get_safe_html('parameters'),
    }

    return render(request, "parameters.html", context)

# ------ Carriers


@login_required
def carriers_view(request, model_uuid):
    """
    View the "Carriers" page

    Parameters:
    model_uuid (uuid): required

    Returns: HttpResponse

    Example:
    http://0.0.0.0:8000/<model_uuid>/carriers/
    """

    model = Model.by_uuid(model_uuid)
    can_edit = model.handle_view_access(request.user)

    context = {
        "model": model,
        "carriers": model.carriers.all(),
        "can_edit": can_edit,
        "help_content": Help_Guide.get_safe_html('carriers'),
    }

    return render(request, "carriers.html", context)

@login_required
def model_flags_view(request, model_uuid):
    """
    View the "Model Flags" page

    Parameters:
    model_uuid (uuid): required

    Returns: HttpResponse

    Example:
    http://0.0.0.0:8000/<model_uuid>/model_flags/
    """

    model = Model.by_uuid(model_uuid)
    can_edit = model.handle_view_access(request.user)

    context = {
        "model": model,
        "tech_params": Tech_Param.objects.filter(model=model,flags__len__gt=0),
        "loc_tech_params": Loc_Tech_Param.objects.filter(model=model,flags__len__gt=0),
        "can_edit": can_edit,
        "help_content": Help_Guide.get_safe_html('carriers'),
    }

    return render(request, "model_flags.html", context)
