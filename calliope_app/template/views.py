import json
from pytz import common_timezones
from django.conf import settings
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_protect
from django.http import JsonResponse, HttpResponse, HttpResponseRedirect
from api.models.configuration import Model, Model_User, Location, Model_Comment
from template.models import Templates, Template_Variables, Template_Types, Template_Type_Variables, Template_Type_Locs, Template_Type_Techs, Template_Type_Loc_Techs, Template_Type_Parameters
from django.urls import reverse

@login_required
@csrf_protect
def model_templates(request):
    """
    Get "Templates" data

    Returns: JsonResponse

    Example:
    GET: /model/templates/
    """
    
    model_uuid = request.GET['model_uuid']
    model = Model.by_uuid(model_uuid)
    templates = list(Templates.objects.all().values('id', 'name', 'template_type', 'model', 'location', 'created', 'updated'))
    template_variables = list(Template_Variables.objects.all().values('id', 'template', 'template_type_variable', 'value', 'timeseries', 'timeseries_meta', 'updated'))

    template_types = list(Template_Types.objects.all().values('id', 'name', 'pretty_name', 'description'))
    template_type_variables = list(Template_Type_Variables.objects.all().values('id', 'name', 'template_type', 'units', 'category', 'choices', 'description', 'timeseries_enabled'))
    template_type_locs = list(Template_Type_Locs.objects.all().values('id', 'name', 'template_type', 'latitude_offset', 'longitude_offset'))
    template_type_techs = list(Template_Type_Techs.objects.all().values('id', 'name', 'template_type', 'abstract_tech', 'carrier_in', 'carrier_out'))
    template_type_loc_techs = list(Template_Type_Loc_Techs.objects.all().values('id', 'name', 'template_type', 'template_loc', 'template_tech'))
    template_type_parameters = list(Template_Type_Parameters.objects.all().values('id', 'template_loc_tech', 'parameter', 'equation'))

    response = {
        'model_uuid ': model_uuid, 
        "templates": templates,
        "template_variables": template_variables,
        "template_types": template_types,
        "template_type_variables": template_type_variables,
        "template_type_locs": template_type_locs,
        "template_type_techs": template_type_techs,
        "template_type_loc_techs": template_type_loc_techs,
        "template_type_parameters": template_type_parameters,
    }

    return JsonResponse(response, safe=False)

@csrf_protect
def add_template(request):
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
    POST: /model/templates/create/
    """

    model_uuid = request.POST["model_uuid"]
    template_id = int(request.POST.get("template_id", 0))
    name = request.POST["name"]
    template_type_name = request.POST["template_type"]
    location_id = request.POST["location"]

    model = Model.by_uuid(model_uuid)
    model.handle_edit_access(request.user)
    template_type = Template_Types.objects.filter(name=template_type_name).first()
    location = Location.objects.filter(id=location_id).first()

    if template_id:
        # Log Activity
        comment = "{} updated a template: {} of template type: {}.".format(
            request.user.get_full_name(),
            name,
            template_type.pretty_name
        )
        Model_Comment.objects.create(model=model, comment=comment, type="add")
        model.notify_collaborators(request.user)
    else:
        template = Templates.objects.create(
            name=name,
            template_type=template_type,
            model=model,
            location=location,
        )

        # Log Activity
        comment = "{} added a template: {} of template type: {}.".format(
            request.user.get_full_name(),
            name,
            template_type.pretty_name
        )
        Model_Comment.objects.create(model=model, comment=comment, type="add")
        model.notify_collaborators(request.user)

    # Return new list of active loc tech IDs
    request.session["template_id"] = template.id
    payload = {"message": "added template",
               "template_id": template.id}

    return HttpResponse(json.dumps(payload), content_type="application/json")