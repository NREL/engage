from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseRedirect
from django.urls import reverse

from api.models.engage import Help_Guide
from api.models.calliope import Parameter, Abstract_Tech
from api.models.configuration import Model, User_File, \
    Technology, Timeseries_Meta, Model_User, Model_Comment

import os
from pytz import common_timezones


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

    comments = Model_Comment.objects.filter(model=model)

    context = {
        "timezones": common_timezones,
        "user": request.user,
        "model": model,
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

    model = Model.by_uuid(model_uuid)
    try:
        can_edit = model.handle_view_access(request.user)
    except Exception:
        return HttpResponseRedirect(reverse('home'))

    context = {
        "pvwatts_api_key": os.getenv("PVWATTS_API_KEY", ""),
        "timezones": common_timezones,
        "model": model,
        "locations": model.locations,
        "mapbox_token": os.getenv("MAPBOX_TOKEN", ""),
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

    technologies = model.technologies
    session_technology_id = request.GET.get('tech_id', None)
    if not session_technology_id:
        session_technology_id = request.session.get('technology_id', None)
    session_technology = technologies.filter(id=session_technology_id).first()

    context = {
        "timezones": common_timezones,
        "model": model,
        "technologies": technologies,
        "session_technology": session_technology,
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

    model = Model.by_uuid(model_uuid)
    try:
        can_edit = model.handle_view_access(request.user)
    except Exception:
        return HttpResponseRedirect(reverse('home'))

    technologies = model.technologies
    session_technology_id = request.GET.get('tech_id', None)
    session_loc_tech_id = request.GET.get('loc_tech_id', None)
    if not session_technology_id:
        session_technology_id = request.session.get('technology_id', None)
    if session_loc_tech_id:
        request.session['loc_tech_id'] = int(session_loc_tech_id)
    session_technology = technologies.filter(id=session_technology_id).first()

    context = {
        "timezones": common_timezones,
        "model": model,
        "technologies": technologies,
        "session_technology": session_technology,
        "can_edit": can_edit,
        "mapbox_token": os.getenv("MAPBOX_TOKEN", ""),
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

    model = Model.by_uuid(model_uuid)
    try:
        can_edit = model.handle_view_access(request.user)
    except Exception:
        return HttpResponseRedirect(reverse('home'))

    scenarios = model.scenarios

    session_scenario_id = request.session.get('scenario_id', None)
    session_scenario = scenarios.filter(id=session_scenario_id).first()

    context = {
        "timezones": common_timezones,
        "model": model,
        "scenarios": scenarios,
        "session_scenario": session_scenario,
        "mapbox_token": os.getenv("MAPBOX_TOKEN", ""),
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
