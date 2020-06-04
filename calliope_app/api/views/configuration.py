from django.views.decorators.csrf import csrf_protect
from django.core.files.storage import FileSystemStorage
from django.shortcuts import redirect
from django.http import HttpResponse
from django.contrib.auth.models import User

from api.models.calliope import Abstract_Tech, Run_Parameter
from api.models.configuration import Location, Technology, Tech_Param, \
    Loc_Tech, Loc_Tech_Param, ParamsManager, Scenario, Scenario_Param, \
    Scenario_Loc_Tech, Timeseries_Meta, Model, Model_Comment, \
    Model_Favorite, User_File, Model_User
from api.tasks import task_status, upload_ts
from taskmeta.models import CeleryTask

import json


# ------ Models ------


@csrf_protect
def add_model(request):
    """
    Create a new model. Option to provide an existing model to copy as a new
    instance. User must already have view access to the template model.

    Parameters:
    template_model_uuid (uuid): optional
    model_name (str): required

    Returns (json): Action Confirmation

    Example:
    POST: /api/add_model/
    """

    user = request.user
    model_name = request.POST["model_name"].strip()
    template_model_uuid = request.POST["template_model_uuid"]

    try:
        template_model = Model.objects.get(uuid=template_model_uuid)
        template_model.handle_view_access(request.user)
    except Exception as e:
        template_model = None
        print("User building from blank model: {}".format(e))

    existing = Model.objects.filter(name__iexact=model_name)
    if len(existing) > 0:
        payload = {"message": "A model with that name already exists."}
    else:
        if template_model is not None:
            model = template_model.duplicate(is_snapshot=False)
            model.name = model_name
            model.save()
            Model_User.objects.filter(model=model).hard_delete()
            comment = (
                "{} {} initiated this model from "
                '<a href="/{}/model/">{}</a>.'.format(
                    user.first_name,
                    user.last_name,
                    template_model.uuid,
                    str(template_model),
                )
            )
            Model_Comment.objects.filter(model=model).hard_delete()
        else:
            model = Model.objects.create(name=model_name)
            comment = "{} initiated this model.".format(
                user.get_full_name()
            )

        Model_User.objects.create(user=request.user,
                                  model=model, can_edit=True)
        Model_Comment.objects.create(model=model,
                                     comment=comment, type="version")
        payload = {"message": "Added model.", "model_uuid": str(model.uuid)}

    return HttpResponse(json.dumps(payload), content_type="application/json")


@csrf_protect
def remove_model(request):
    """
    Removes a user's access to a model. The model will still exist and
    may be seen by other collaborators.

    Parameters:
    model_uuid (uuid): required

    Returns (json): Action Confirmation

    Example:
    POST: /api/remove_model/
    """

    user = request.user
    model_uuid = request.POST["model_uuid"]

    model = Model.by_uuid(model_uuid)
    model.handle_view_access(request.user)

    Model_User.objects.filter(model=model, user=user).hard_delete()
    payload = {"message": "Dropped as collaborator."}

    return HttpResponse(json.dumps(payload), content_type="application/json")


@csrf_protect
def duplicate_model(request):
    """
    Duplicate a model as a view only snapshot. User's may choose to take a
    snapshot of a model to provide a retrieval checkpoint and/or begin a
    forked version of their original model. A snapshot will replicate all of
    its underlying data as new instances.

    Parameters:
    model_uuid (uuid): required

    Returns (json): Action Confirmation

    Example:
    POST: /api/duplicate_model/
    """

    user = request.user
    model_uuid = request.POST["model_uuid"]

    old_model = Model.by_uuid(model_uuid)
    old_model.handle_edit_access(user)

    new_model = old_model.duplicate(is_snapshot=True)

    # Log Activity
    old_comment = '{} created a snapshot: <a href="/{}/model/">{}</a>'
    old_comment = old_comment.format(user.get_full_name(),
                                     new_model.uuid,
                                     str(new_model))
    new_comment = ('{} {} created this snapshot based on, '
                   '<a href="/{}/model/">{}</a>.')
    new_comment = new_comment.format(user.first_name,
                                     user.last_name,
                                     old_model.uuid,
                                     str(old_model))
    Model_Comment.objects.create(model=old_model,
                                 comment=old_comment, type="version")
    Model_Comment.objects.create(model=new_model,
                                 comment=new_comment, type="version")

    payload = {
        "message": "duplicated model",
        "old_model_uuid": str(old_model.uuid),
        "new_model_uuid": str(new_model.uuid),
    }

    return HttpResponse(json.dumps(payload), content_type="application/json")


@csrf_protect
def add_collaborator(request):
    """
    Add a collaborator to a model. A collaborator may become:
    granted of edit permissions (value=1),
    granted of view only permissions (value=0),
    removed of all permisssions (value=null)

    Parameters:
    model_uuid (uuid): required
    collaborator_email (str): required
    collaborator_can_edit (int): optional (0 or 1)

    Returns (json): Action Confirmation

    Example:
    POST: /api/add_collaborator/
    """

    model_uuid = request.POST["model_uuid"]
    email = request.POST["collaborator_email"]
    user = User.objects.filter(email=email).first()
    try:
        can_edit = bool(int(request.POST["collaborator_can_edit"]))
    except ValueError:
        can_edit = None

    model = Model.by_uuid(model_uuid)
    model.handle_edit_access(request.user)

    if user:
        message = Model_User.update(model, user, can_edit)
    else:
        message = "No user registered by that email."

    payload = {"message": message}

    return HttpResponse(json.dumps(payload), content_type="application/json")


@csrf_protect
def add_model_comment(request):
    """
    Add a user comment to a model's activity page

    Parameters:
    model_uuid (uuid): required
    comment (str): required

    Returns (json): Action Confirmation

    Example:
    POST: /api/add_model_comment/
    """

    model_uuid = request.POST["model_uuid"]
    comment = request.POST["comment"]

    model = Model.by_uuid(model_uuid)
    model.handle_edit_access(request.user)

    if len(comment) > 0:
        Model_Comment.objects.create(
            model=model, user=request.user, comment=comment, type="comment"
        )
        model.notify_collaborators(request.user)
        payload = {"message": "Added comment."}
    else:
        payload = {"message": "No comment to be added."}

    return HttpResponse(json.dumps(payload), content_type="application/json")


# ------ Locations


@csrf_protect
def update_location(request):
    """
    Add or Update a location.
    To update a location, must provide a location_id

    Parameters:
    model_uuid (uuid): required
    location_id (int): optional
    location_name (str): required
    location_lat (float): required
    location_long (float): required
    location_area (float): required
    location_description (str): required

    Returns (json): Action Confirmation

    Example:
    POST: /api/update_location/
    """

    model_uuid = request.POST["model_uuid"]
    location_id = int(request.POST.get("location_id", 0))
    location_name = request.POST["location_name"].strip()
    location_lat = float(request.POST["location_lat"])
    location_long = float(request.POST["location_long"])
    location_area = request.POST["location_area"]
    location_description = request.POST["location_description"]

    model = Model.by_uuid(model_uuid)
    model.handle_edit_access(request.user)

    if location_area == "":
        location_area = None
    elif float(location_area) < 0:
        location_area = None
    if ((location_lat < -90) or (location_lat > 90)):
        location_lat = 0
    if ((location_long < -180) or (location_long > 180)):
        location_long = 0

    non_unique_name = True
    while non_unique_name:
        existing = model.locations.filter(pretty_name__iexact=location_name)
        if existing:
            if location_id == existing.first().id:
                non_unique_name = False
            else:
                location_name += " COPY"
        else:
            non_unique_name = False

    if location_id:
        model.locations.filter(id=location_id).update(
            pretty_name=location_name,
            name=ParamsManager.simplify_name(location_name),
            latitude=location_lat,
            longitude=location_long,
            available_area=location_area,
            description=location_description,
        )
        # Log Activity
        comment = "{} updated the location: {}.".format(
            request.user.get_full_name(), location_name
        )
        Model_Comment.objects.create(model=model, comment=comment, type="edit")
        model.notify_collaborators(request.user)
        model.deprecate_runs(location_id=location_id)

        payload = {
            "message": "edited location",
            "location_id": location_id,
            "location_name": location_name,
            "location_lat": location_lat,
            "location_long": location_long,
            "location_area": location_area,
            "location_description": location_description,
        }

    else:
        location = Location.objects.create(
            model_id=model.id,
            pretty_name=location_name,
            name=ParamsManager.simplify_name(location_name),
            latitude=location_lat,
            longitude=location_long,
            available_area=location_area,
            description=location_description,
        )
        # Log Activity
        comment = "{} added a location: {}.".format(
            request.user.get_full_name(), location_name
        )
        Model_Comment.objects.create(model=model, comment=comment, type="add")
        model.notify_collaborators(request.user)

        payload = {
            "message": "added location",
            "location_id": location.id,
            "location_name": location_name,
            "location_lat": location_lat,
            "location_long": location_long,
            "location_area": location_area,
            "location_description": location_description,
        }

    return HttpResponse(json.dumps(payload), content_type="application/json")


@csrf_protect
def delete_location(request):
    """
    Delete a location. This action will cascade "delete" all instances that
    refer to it.

    Parameters:
    model_uuid (uuid): required
    location_id (int): required

    Returns (json): Action Confirmation

    Example:
    POST: /api/delete_location/
    """

    model_uuid = request.POST["model_uuid"]
    location_id = request.POST["location_id"]

    model = Model.by_uuid(model_uuid)
    model.handle_edit_access(request.user)

    locations = model.locations.filter(id=location_id)
    if len(locations) > 0:
        pretty_name = locations.first().pretty_name
        model.deprecate_runs(location_id=location_id)
        locations.delete()
        # Log Activity
        comment = "{} deleted the location: {}.".format(
            request.user.get_full_name(), pretty_name
        )
        Model_Comment.objects.create(model=model,
                                     comment=comment, type="delete")
        model.notify_collaborators(request.user)

    payload = {"message": "deleted location"}

    return HttpResponse(json.dumps(payload), content_type="application/json")


# ------ Technologies


@csrf_protect
def add_technology(request):
    """
    Add a new technology. Option to create technology from an existing
    technology to inherit its technology level parameters. Any override
    parameters set at the nodes level will not be transferred.

    Parameters:
    model_uuid (uuid): required
    technology_pretty_name (str): required
    technology_type (str): required
    technology_id (int): optional

    Returns (json): Action Confirmation

    Example:
    POST: /api/add_technolgy/
    """

    model_uuid = request.POST["model_uuid"]
    technology_pretty_name = request.POST["technology_name"]
    technology_id = request.POST.get("technology_id", None)
    technology_type = request.POST["technology_type"]

    model = Model.by_uuid(model_uuid)
    model.handle_edit_access(request.user)

    abstract_tech = Abstract_Tech.objects.filter(name=technology_type).first()
    technology_name = ParamsManager.simplify_name(technology_pretty_name)

    if technology_id is not None:
        existing = Technology.objects.filter(id=technology_id).first()
        existing.model.handle_view_access(request.user)
        technology = existing.duplicate(model.id, technology_pretty_name)
    else:
        technology = Technology.objects.create(
            model_id=model.id,
            abstract_tech_id=abstract_tech.id,
            name=technology_name,
            pretty_name=technology_pretty_name,
        )
        Tech_Param.objects.create(
            model_id=model.id,
            technology_id=technology.id,
            parameter_id=1,
            value=technology_type,
        )
        Tech_Param.objects.create(
            model_id=model.id,
            technology_id=technology.id,
            parameter_id=2,
            value=technology_pretty_name,
        )
    # Log Activity
    comment = "{} added a technology: {}.".format(
        request.user.get_full_name(), technology_pretty_name
    )
    Model_Comment.objects.create(model=model, comment=comment, type="add")
    model.notify_collaborators(request.user)

    request.session["technology_id"] = technology.id
    payload = {"message": "added technology", "technology_id": technology.id}

    return HttpResponse(json.dumps(payload), content_type="application/json")


@csrf_protect
def delete_technology(request):
    """
    Delete a technology. This action will cascade "delete" all instances that
    refer to it.

    Parameters:
    model_uuid (uuid): required
    technology_id (int): required

    Returns (json): Action Confirmation

    Example:
    POST: /api/delete_technology/
    """

    model_uuid = request.POST["model_uuid"]
    technology_id = request.POST["technology_id"]

    model = Model.by_uuid(model_uuid)
    model.handle_edit_access(request.user)

    technologies = model.technologies.filter(id=technology_id)
    if len(technologies) > 0:
        technology_pretty_name = technologies.first().pretty_name
        model.deprecate_runs(technology_id=technology_id)
        technologies.delete()
        # Log Activity
        comment = "{} deleted the technology: {}.".format(
            request.user.get_full_name(), technology_pretty_name
        )
        Model_Comment.objects.create(model=model,
                                     comment=comment, type="delete")
        model.notify_collaborators(request.user)
    payload = {"message": "deleted technology"}

    return HttpResponse(json.dumps(payload), content_type="application/json")


@csrf_protect
def update_tech_params(request):
    """
    Update the parameters for a technology. Parameter data is provided in a
    form_data object which stores updates under the following keys:
        'essentials', 'add', 'edit', 'delete', 'is_linear', 'is_expansion'

    Parameters:
    model_uuid (uuid): required
    technology_id (int): required
    form_data (json): required

    Returns (json): Action Confirmation

    Example:
    POST: /api/update_tech_params/
    """

    model_uuid = request.POST["model_uuid"]
    technology_id = request.POST["technology_id"]
    form_data = json.loads(request.POST["form_data"])

    model = Model.by_uuid(model_uuid)
    model.handle_edit_access(request.user)

    technology = model.technologies.filter(id=technology_id)

    if len(technology) > 0:
        technology.first().update(form_data)
        # Log Activity
        comment = "{} updated the technology: {}.".format(
            request.user.get_full_name(),
            technology.first().pretty_name,
        )
        Model_Comment.objects.create(model=model, comment=comment, type="edit")
        model.notify_collaborators(request.user)
        model.deprecate_runs(technology_id=technology_id)
    payload = {"message": "Success."}

    return HttpResponse(json.dumps(payload), content_type="application/json")


@csrf_protect
def update_favorite(request):
    """
    Add a parameter as a favorite. Favorites are persisted on a model by model
    basis. Therefore, if one user adds or removes a favorite parameter,
    all collaborators on that model will experience those changes.

    Parameters:
    model_uuid (uuid): required
    param_id (int): required
    add_favorite (int): required

    Returns (json): Action Confirmation

    Example:
    GET: /api/update_favorite/
    """

    model_uuid = request.GET["model_uuid"]
    add_favorite = int(request.GET["add_favorite"])
    param_id = int(request.GET["param_id"])

    model = Model.by_uuid(model_uuid)
    model.handle_edit_access(request.user)

    if add_favorite:
        Model_Favorite.objects.create(model_id=model.id, parameter_id=param_id)
        payload = {"message": "added favorite"}
    else:
        Model_Favorite.objects.filter(model_id=model.id,
                                      parameter_id=param_id).hard_delete()
        payload = {"message": "removed favorite"}

    return HttpResponse(json.dumps(payload), content_type="application/json")


@csrf_protect
def convert_to_timeseries(request):
    """
    Convert a static parameter into a timeseries. Note that this does not yet
    assign a timeseries meta instance to the parameter instance. Any previous
    data that has been configured for this parameter will be lost.

    Parameters:
    model_uuid (uuid): required
    technology_id (int): required
    param_id (int): required

    Returns (json): Action Confirmation

    Example:
    GET: /api/convert_to_timeseries/
    """

    model_uuid = request.GET["model_uuid"]
    param_id = int(request.GET["param_id"])
    technology_id = request.GET["technology_id"]
    try:
        loc_tech_id = int(request.GET["loc_tech_id"])
    except Exception as e:
        loc_tech_id = None
        print("Technology only: {}".format(e))

    model = Model.by_uuid(model_uuid)
    model.handle_edit_access(request.user)

    if loc_tech_id:
        Loc_Tech_Param.objects.filter(
            model_id=model.id, parameter_id=param_id, loc_tech_id=loc_tech_id
        ).hard_delete()
        Loc_Tech_Param.objects.create(
            model_id=model.id,
            parameter_id=param_id,
            loc_tech_id=loc_tech_id,
            value=0,
            timeseries=True,
        )
        payload = {"message": "added timeseries to node"}
    else:
        Tech_Param.objects.filter(model_id=model.id,
                                  parameter_id=param_id,
                                  technology_id=technology_id).hard_delete()
        Tech_Param.objects.create(
            model_id=model.id,
            parameter_id=param_id,
            technology_id=technology_id,
            value=0,
            timeseries=True,
        )
        payload = {"message": "added timeseries to technology"}

    return HttpResponse(json.dumps(payload), content_type="application/json")


# ------ Location-Technologies (Nodes)


@csrf_protect
def add_loc_tech(request):
    """
    Add a new node (location + technology). An argument for location_2_id is
    only required for nodes with a transmission technology.

    Parameters:
    model_uuid (uuid): required
    technology_id (int): required
    location_1_id (int): required
    location_2_id (int): optional
    loc_tech_description (str): optional

    Returns (json): Action Confirmation

    Example:
    POST: /api/add_loc_tech/
    """

    model_uuid = request.POST["model_uuid"]
    technology_id = request.POST["technology_id"]
    location_1_id = request.POST["location_1_id"]
    location_2_id = request.POST.get("location_2_id", None)
    loc_tech_description = request.POST.get("loc_tech_description", None)

    model = Model.by_uuid(model_uuid)
    model.handle_edit_access(request.user)

    technology = model.technologies.filter(id=technology_id).first()
    location_1 = model.locations.filter(id=location_1_id).first()
    location_2 = model.locations.filter(id=location_2_id).first()
    if technology.abstract_tech.name != "transmission":
        location_2_id = None

    existing = model.loc_techs.filter(
        technology=technology,
        location_1=location_1,
        location_2=location_2,
    )
    if existing.first():
        loc_tech = existing.first()

    else:
        loc_tech = Loc_Tech.objects.create(
            model=model,
            technology=technology,
            location_1=location_1,
            location_2=location_2,
            description=loc_tech_description,
        )
    # Log Activity
    comment = "{} added a node: {} ({}) @ {}.".format(
        request.user.get_full_name(),
        technology.pretty_name,
        technology.tag,
        location_1.pretty_name,
    )
    Model_Comment.objects.create(model=model, comment=comment, type="add")
    model.notify_collaborators(request.user)

    request.session["loc_tech_id"] = loc_tech.id
    payload = {"message": "added location technology",
               "loc_tech_id": loc_tech.id}

    return HttpResponse(json.dumps(payload), content_type="application/json")


@csrf_protect
def delete_loc_tech(request):
    """
    Delete a node (location + technology). This action will cascade "delete"
    all instances that refer to it.

    Parameters:
    model_uuid (uuid): required
    loc_tech_id (int): required

    Returns (json): Action Confirmation

    Example:
    POST: /api/delete_loc_tech/
    """

    model_uuid = request.POST["model_uuid"]
    loc_tech_id = request.POST["loc_tech_id"]

    model = Model.by_uuid(model_uuid)
    model.handle_edit_access(request.user)

    loc_techs = model.loc_techs.filter(id=loc_tech_id)
    # Log Activity
    comment = "{} deleted the node: {} ({}) @ {}.".format(
        request.user.get_full_name(),
        loc_techs.first().technology.pretty_name,
        loc_techs.first().technology.tag,
        loc_techs.first().location_1.pretty_name,
    )
    Model_Comment.objects.create(model=model, comment=comment, type="delete")
    model.notify_collaborators(request.user)
    model.deprecate_runs(technology_id=loc_techs.first().technology_id)

    loc_techs.delete()
    payload = {"message": "deleted location technology"}

    return HttpResponse(json.dumps(payload), content_type="application/json")


@csrf_protect
def update_loc_tech_params(request):
    """
    Update the parameters for a node. Parameter data is provided in a
    form_data object which stores updates under the following keys:
        'add', 'edit', 'delete'

    Parameters:
    model_uuid (uuid): required
    loc_tech_id (int): required
    form_data (json): required

    Returns (json): Action Confirmation

    Example:
    POST: /api/update_loc_tech_params/
    """

    model_uuid = request.POST["model_uuid"]
    loc_tech_id = request.POST["loc_tech_id"]
    form_data = json.loads(request.POST["form_data"])

    model = Model.by_uuid(model_uuid)
    model.handle_edit_access(request.user)

    loc_tech = model.loc_techs.filter(id=loc_tech_id)

    if len(loc_tech) > 0:
        loc_tech.first().update(form_data)
        # Log Activity
        comment = "{} updated the node: {} ({}) @ {}.".format(
            request.user.get_full_name(),
            loc_tech.first().technology.pretty_name,
            loc_tech.first().technology.tag,
            loc_tech.first().location_1.pretty_name,
        )
        Model_Comment.objects.create(model=model, comment=comment, type="edit")
        model.notify_collaborators(request.user)
        model.deprecate_runs(technology_id=loc_tech.first().technology_id)
    payload = {"message": "Success."}

    return HttpResponse(json.dumps(payload), content_type="application/json")


# ------ Scenarios


@csrf_protect
def add_scenario(request):
    """
    Create a new scenario. Option to create a new scenario from an existing one
    by providing an existing scenario_id. Configuration and settings will be
    copied as new instances.

    Parameters:
    model_uuid (uuid): required
    scenario_name (str): required
    scenario_id (str): optional

    Returns (json): Action Confirmation

    Example:
    POST: /api/add_scenario/
    """

    model_uuid = request.POST["model_uuid"]
    scenario_id = request.POST.get("scenario_id", None)
    scenario_name = request.POST["scenario_name"]

    model = Model.by_uuid(model_uuid)
    model.handle_edit_access(request.user)

    if scenario_id not in [None, '']:
        existing = model.scenarios.filter(id=scenario_id).first()
        scenario = existing.duplicate(scenario_name)
    else:
        scenario = Scenario.objects.create(model_id=model.id,
                                           name=scenario_name)
        parameters = Run_Parameter.objects.all()
        for param in parameters:
            if param.name == "name":
                value = "{}: {}".format(model.name, scenario_name)
            else:
                value = param.default_value
            Scenario_Param.objects.create(
                scenario=scenario, run_parameter=param,
                value=value, model=model
            )

    # Log Activity
    comment = "{} added a scenario: {}.".format(
        request.user.get_full_name(), scenario_name
    )
    Model_Comment.objects.create(model=model, comment=comment, type="add")
    model.notify_collaborators(request.user)

    request.session["scenario_id"] = scenario.id

    payload = {"message": "added scenario", "scenario_id": scenario.id}

    return HttpResponse(json.dumps(payload), content_type="application/json")


@csrf_protect
def toggle_scenario_loc_tech(request):
    """
    Add/remove a node (loc_tech) to/from a scenario.

    Parameters:
    model_uuid (uuid): required
    scenario_id (int): required
    loc_tech_id (int): required
    add (int): required: 1-True, 0-False

    Returns (json): Action Confirmation

    Example:
    POST: /api/toggle_scenario_loc_tech/
    """

    model_uuid = request.POST["model_uuid"]
    scenario_id = request.POST["scenario_id"]
    loc_tech_id = request.POST["loc_tech_id"]
    add = bool(int(request.POST["add"]))

    model = Model.by_uuid(model_uuid)
    model.handle_edit_access(request.user)

    scenario = model.scenarios.filter(id=scenario_id).first()
    scenario_loc_tech = Scenario_Loc_Tech.objects.filter(
        model_id=model.id, scenario_id=scenario_id, loc_tech_id=loc_tech_id
    ).first()

    if add:
        if not scenario_loc_tech:
            scenario_loc_tech = Scenario_Loc_Tech.objects.create(
                model_id=model.id, scenario_id=scenario_id,
                loc_tech_id=loc_tech_id
            )
            payload = {
                "message": "added scenario location technology",
                "scenario_loc_tech_id": scenario_loc_tech.id,
            }
        else:
            payload = {
                "message": "scenario location technology already exists",
                "scenario_loc_tech_id": scenario_loc_tech.id,
            }
            print("------- Client Error: Already Exists")
    elif not add:
        if not scenario_loc_tech:
            payload = {"message": "scenario location technology doesn' exist."}
            print("------- Client Error: Doesn't Exist")
        else:
            scenario_loc_tech_id = scenario_loc_tech.id
            scenario_loc_tech.delete()
            payload = {
                "message": "removed scenario location technology",
                "scenario_loc_tech_id": scenario_loc_tech_id,
            }
    # Log Activity
    comment = "{} updated the scenario: {}.".format(
        request.user.get_full_name(), scenario.name
    )
    Model_Comment.objects.filter(model=model,
                                 comment=comment, type="edit").hard_delete()
    Model_Comment.objects.create(model=model, comment=comment, type="edit")
    model.deprecate_runs(scenario_id=scenario_id)

    return HttpResponse(json.dumps(payload), content_type="application/json")


@csrf_protect
def update_scenario_params(request):
    """
    Update the parameters on a scenario. Parameter data is provided in a
    form_data object which stores updates under the following keys:
        'add', 'edit', 'delete'

    Parameters:
    model_uuid (uuid): required
    scenario_id (int): required
    form_data (json): required

    Returns (json): Action Confirmation

    Example:
    POST: /api/update_scenario_params/
    """

    model_uuid = request.POST["model_uuid"]
    scenario_id = request.POST["scenario_id"]
    form_data = json.loads(request.POST["form_data"])

    model = Model.by_uuid(model_uuid)
    model.handle_edit_access(request.user)

    scenario = model.scenarios.filter(id=scenario_id).first()
    Scenario_Param.update(scenario, form_data)

    # Log Activity
    comment = "{} updated the scenario: {}.".format(
        request.user.get_full_name(), scenario.name
    )
    Model_Comment.objects.create(model=model, comment=comment, type="edit")
    model.notify_collaborators(request.user)
    model.deprecate_runs(scenario_id=scenario_id)

    payload = {"message": "Success."}

    return HttpResponse(json.dumps(payload), content_type="application/json")


@csrf_protect
def delete_scenario(request):
    """
    Delete a scenario. This action will cascade "delete" all instances that
    refer to it.

    Parameters:
    model_uuid (uuid): required
    scenario_id (int): required

    Returns (json): Action Confirmation

    Example:
    POST: /api/delete_scenario/
    """

    model_uuid = request.POST["model_uuid"]
    scenario_id = request.POST["scenario_id"]

    model = Model.by_uuid(model_uuid)
    model.handle_edit_access(request.user)

    scenarios = model.scenarios.filter(id=scenario_id)
    if len(scenarios) > 0:
        name = scenarios.first().name
        scenarios.delete()
        # Log Activity
        comment = "{} deleted the scenario: {}.".format(
            request.user.get_full_name(), name
        )
        Model_Comment.objects.create(model=model,
                                     comment=comment, type="delete")
        model.notify_collaborators(request.user)

    payload = {"message": "deleted scenario"}

    return HttpResponse(json.dumps(payload), content_type="application/json")


# ------ Timeseries


@csrf_protect
def upload_file(request):
    """
    Upload a timeseries file.

    Parameters:
    model_uuid (uuid): required
    description (str): optional
    myfile (file): required

    Returns: Redirect to the timeseries page for the given model

    Example:
    POST: /api/upload_file/
    """

    model_uuid = request.POST["model_uuid"]
    description = request.POST.get("file-description", None)

    model = Model.by_uuid(model_uuid)
    model.handle_edit_access(request.user)

    if (request.method == "POST") and ("myfile" in request.FILES):

        myfile = request.FILES["myfile"]
        fs = FileSystemStorage()
        filename = fs.save("user_files/" + myfile.name, myfile)
        User_File.objects.create(filename=filename,
                                 description=description, model=model)

        return redirect("/%s/timeseries/" % model_uuid)

    return redirect("/{}/timeseries/".format(model_uuid))


@csrf_protect
def delete_timeseries(request):
    """
    Delete a timeseries

    Parameters:
    model_uuid (uuid): required
    timeseries_id (int): required

    Returns (json): Action Confirmation

    Example:
    POST: /api/delete_timeseries/
    """

    model_uuid = request.POST.get("model_uuid", None)
    timeseries_id = request.POST.get("timeseries_id", None)

    model = Model.by_uuid(model_uuid)
    model.handle_edit_access(request.user)

    timeseries_meta = Timeseries_Meta.objects.filter(
        model=model, id=timeseries_id
    )
    timeseries_meta.delete()

    payload = {"message": "Success."}

    return HttpResponse(json.dumps(payload), content_type="application/json")


@csrf_protect
def delete_file(request):
    """
    Delete a user timeseries file

    Parameters:
    model_uuid (uuid): required
    file_id (int): required

    Returns (json): Action Confirmation

    Example:
    POST: /api/delete_file/
    """

    model_uuid = request.POST.get("model_uuid", None)
    file_id = request.POST.get("file_id", None)

    model = Model.by_uuid(model_uuid)
    model.handle_edit_access(request.user)

    file_record = User_File.objects.filter(model=model, id=file_id)

    file_record.delete()
    payload = {"message": "Success."}

    return HttpResponse(json.dumps(payload), content_type="application/json")


@csrf_protect
def import_timeseries(request):
    """
    Import a timeseries

    Parameters:
    model_uuid (uuid): required
    timeseries_id (int): required

    Returns (json): Action Confirmation

    Example:
    POST: /api/import_timeseries/
    """

    model_uuid = request.POST["model_uuid"]
    name = request.POST["name"]
    values = request.POST["timeseries"].split(',')

    model = Model.by_uuid(model_uuid)
    model.handle_edit_access(request.user)

    Timeseries_Meta.create_ts_8760(model, name, values)

    payload = {"message": "Success."}

    return HttpResponse(json.dumps(payload), content_type="application/json")


@csrf_protect
def upload_timeseries(request):
    """
    Build and save a clean timeseries csv from a user uploaded file.

    Parameters:
    model_uuid (uuid): required
    file_id (int): required
    timeseries_name (str): required
    timestamp_col (int): required
    value_col (int): required
    has_header (bool): required

    Returns (json): Action Confirmation

    Example:
    GET: /api/upload_timeseries/
    """

    model_uuid = request.GET.get("model_uuid", None)
    file_id = request.GET.get("file_id", None)
    timeseries_name = request.GET.get("timeseries_name", None)
    timestamp_col = request.GET.get("timestamp_col", None)
    value_col = request.GET.get("value_col", None)
    has_header = request.GET.get("has_header", None)

    if has_header == "true":
        has_header = True
    else:
        has_header = False

    model = Model.by_uuid(model_uuid)
    model.handle_edit_access(request.user)

    file_record = User_File.objects.filter(model=model, id=file_id)
    simple_filename = file_record.first().simple_filename()

    payload = {}
    existing = Timeseries_Meta.objects.filter(model=model,
                                              name=timeseries_name).first()
    if existing:
        payload["status"] = task_status.FAILURE
        payload["message"] = "Timeseries name already exists"
        return HttpResponse(json.dumps(payload),
                            content_type="application/json")

    new_meta = Timeseries_Meta.objects.create(
        model=model,
        name=timeseries_name,
        original_filename=simple_filename,
        original_timestamp_col=timestamp_col,
        original_value_col=value_col,
    )
    try:
        async_result = upload_ts.apply_async(
            kwargs={
                "model_uuid": model_uuid,
                "timeseries_meta_id": new_meta.id,
                "file_id": file_id,
                "timestamp_col": timestamp_col,
                "value_col": value_col,
                "has_header": has_header,
            }
        )
        upload_task, _ = CeleryTask.objects.get_or_create(
            task_id=async_result.id)

        new_meta.upload_task = upload_task
        new_meta.is_uploading = True
        new_meta.save()
        payload["status"] = "Success"
        # Only means that the submission of the celery task was successful.

    except Exception as e:
        print(e)
        payload["status"] = "Failed"
        payload["message"] = str(e)
        if not has_header:
            payload["message"] += (
                " Please try checking the box, "
                '"The first row of the selected CSV file is a header row."'
            )
        new_meta.delete()

    return HttpResponse(json.dumps(payload), content_type="application/json")
