import json
import os
import re
import logging
from datetime import date
from django.core.mail import send_mail
import numpy as np
from django.conf import settings
from django.views.decorators.csrf import csrf_protect
from django.core.files.storage import FileSystemStorage
from django.shortcuts import redirect
from django.http import HttpResponse, FileResponse
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.utils.html import escape
from PySAM import Windpower
from PySAM.ResourceTools import FetchResourceFiles
from django_ratelimit.decorators import ratelimit
from api.models.engage import RequestRateLimit
from api.models.calliope import Abstract_Tech, Run_Parameter
from api.models.configuration import Location, Technology, Tech_Param, \
    Loc_Tech, Loc_Tech_Param, ParamsManager, Scenario, Scenario_Param, \
    Scenario_Loc_Tech, Timeseries_Meta, Model, Model_Comment, \
    Model_Favorite, User_File, Model_User, Carrier
from api.tasks import task_status, upload_ts, copy_model
from api.utils import recursive_escape
from taskmeta.models import CeleryTask

logger = logging.getLogger(__name__)

def validate_model_name(value):
    if len(value) < 3:
        raise ValidationError(f"Error: Invalid model name, too short.")

    regex = re.compile(r"(<(.*)>.*?|<(.*) />|[^\w\s\(\)-])")
    matched = regex.search(value)
    if matched is None:
        return

    diff = set(value).difference(set(["(", ")", " ", "-", "_"]))
    if len(diff) == 0:
        raise ValidationError("Error: Invalid model name, should not contain only symbols")

    result = matched.group(0)
    raise ValidationError(f"Error: Invalid model name, should not contain '{result}'")


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
    payload = {}

    try:
        validate_model_name(model_name)
    except ValidationError as e:
        payload["status"] = "Failed"
        payload["message"] = str(e)
        return HttpResponse(json.dumps(payload), content_type="application/json")

    try:
        template_model = Model.objects.get(uuid=template_model_uuid)
        template_model.handle_view_access(user)
    except Exception as e:
        template_model = None
        print("User building from blank model: {}".format(e))

    # Create Model
    model_name = Model.find_unique_name(model_name)
    model = Model.objects.create(name=model_name)
    Model_User.objects.create(user=user, model=model, can_edit=True)
    comment = "{} initiated this model.".format(user.get_full_name())
    Model_Comment.objects.create(model=model, comment=comment, type="version")
    payload['model_uuid'] = str(model.uuid)
    payload["status"] = "Added"

    if template_model is not None:
        try:
            model.is_uploading = True
            model.save()
            copy_model.apply_async(
                kwargs={"src_model_id": template_model.id,
                        "dst_model_id": model.id,
                        "user_id": user.id})
            payload["status"] = "Submitted"
        except Exception as e:
            payload["status"] = "Failed"
            payload["message"] = str(e)
            model.delete()

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
    payload = {}

    old_model = Model.by_uuid(model_uuid)
    old_model.handle_edit_access(user)

    # Create Model
    model = Model.objects.create(name=old_model.name)
    latest = Model.objects.filter(name=model.name).exclude(
        snapshot_version=None).values_list('snapshot_version',
                                           flat=True)
    model.snapshot_version = np.max(list(latest) + [0]) + 1
    model.snapshot_base = old_model
    payload['model_uuid'] = str(model.uuid)
    model.save()

    try:
        model.is_uploading = True
        model.save()
        copy_model.apply_async(
            kwargs={"src_model_id": old_model.id,
                    "dst_model_id": model.id,
                    "user_id": user.id})
        payload["status"] = "Submitted"
    except Exception as e:
        payload["status"] = "Failed"
        payload["message"] = str(e)
        model.delete()

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
    collaborator_id (str): required
    collaborator_can_edit (int): optional (0 or 1)

    Returns (json): Action Confirmation

    Example:
    POST: /api/add_collaborator/
    """

    model_uuid = request.POST["model_uuid"]
    user_id = request.POST["collaborator_id"]
    user = User.objects.filter(id=user_id).first()
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


def validate_model_comment(value):
    value = value.strip()
    if len(value) == 0:
        raise ValidationError("Please write your comment.")

    regex = re.compile(r"(<(.*)>.*?|<(.*) />)")
    matched = regex.search(value)
    if matched is None:
        return

    result = matched.group(0)
    raise ValidationError(f"Invalid comment string, please remove '{result}'")


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

    try:
        validate_model_comment(comment)
        comment = escape(comment)  # Reference: https://docs.djangoproject.com/en/3.2/ref/utils/#module-django.utils.html
    except ValidationError as e:
        payload = {"message": str(e)}
        return HttpResponse(json.dumps(payload), content_type="application/json")

    model = Model.by_uuid(model_uuid)
    model.handle_edit_access(request.user)

    Model_Comment.objects.create(
        model=model, user=request.user, comment=comment, type="comment"
    )
    model.notify_collaborators(request.user)
    payload = {"message": "Added comment."}

    return HttpResponse(json.dumps(payload), content_type="application/json")

@csrf_protect
def update_carriers(request):
    """
    Update a models carriers with changes/additions/deletions

    Parameters:
    model_uuid (uuid): required
    form_data (json): required

    Returns (json): Action Confirmation

    Example:
    POST: /api/update_carriers/
    """

    model_uuid = request.POST["model_uuid"]
    form_data = json.loads(request.POST["form_data"])
    model = Model.by_uuid(model_uuid)
    err_msg = ''
    flags = False
    if 'edit' in form_data:
        for i,c in form_data['edit'].items():
            if i != 'new':
                carrier = Carrier.objects.filter(model=model,name=c['carrier-name']).first()
                carrier.rate_unit = c['carrier-rate']
                carrier.quantity_unit = c['carrier-quantity']
                carrier.description = c['carrier-desc']
                carrier.save()
                model.check_model_carrier_units(carrier)
                flags = True
            else:
                try:
                    carrier = Carrier.objects.create(model=model,name=c['carrier-name'],rate_unit=c['carrier-rate'],quantity_unit=c['carrier-quantity'],description=c.get('carrier-desc',''))
                    if carrier.name in model.carriers_old:
                        model.check_model_carrier_units(carrier)
                        flags = True
                except Exception as e:
                    err_msg += str(e)

    if 'delete' in form_data:
        for i,c in form_data['delete']['carrier'].items():
            Carrier.objects.filter(id=i).delete()

    if err_msg != '':
        payload = {"message": err_msg}
    else:
        payload = {"message": "Success.", "flags":flags}

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
    location_name = escape(request.POST["location_name"].strip())
    location_lat = float(request.POST["location_lat"])
    location_long = float(request.POST["location_long"])
    location_area = escape(request.POST["location_area"])
    location_description = escape(request.POST["location_description"])

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
 