import json
from pytz import common_timezones
from django.conf import settings
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_protect
from django.http import JsonResponse, HttpResponse
from api.models.configuration import Model, Model_User
from template.models import Templates, Template_Variables, Template_Types, Template_Type_Variables, Template_Type_Locs, Template_Type_Techs, Template_Type_Loc_Techs, Template_Type_Parameters
from django.core.serializers import serialize
from django.core.serializers.json import DjangoJSONEncoder

class LazyEncoder(DjangoJSONEncoder):
    def default(self, obj):
        if isinstance(obj, Template_Types):
            return str(obj)
        return super().default(obj)

@login_required
@csrf_protect
def templates_admin_view(request):
    """
    Get "Templates" data

    Returns: JsonResponse

    Example:
    GET: /templates/model/
    """
    
    model_uuid = request.GET['model_uuid']
    #model = Model.by_uuid(model_uuid)
    
    templates = list(Templates.objects.all().values('name', 'template_type', 'model', 'location', 'created', 'updated'))
    template_variables = list(Template_Variables.objects.all().values('template', 'template_type_variable', 'value', 'timeseries', 'timeseries_meta', 'updated'))

    template_types = list(Template_Types.objects.all().values('name', 'pretty_name', 'description'))
    #template_types = serialize('jsonl', Template_Types.objects.all(), cls=LazyEncoder)
    template_type_variables = list(Template_Type_Variables.objects.all().values('name', 'template_type', 'units', 'default_value', 'description', 'timeseries_enabled'))
    template_type_locs = list(Template_Type_Locs.objects.all().values('name', 'template_type', 'latitude_offset', 'longitude_offset'))
    template_type_techs = list(Template_Type_Techs.objects.all().values('name', 'template_type', 'abstract_tech', 'carrier_in', 'carrier_out'))
    template_type_loc_techs = list(Template_Type_Loc_Techs.objects.all().values('name', 'template_type', 'template_loc', 'template_tech'))
    template_type_parameters = list(Template_Type_Parameters.objects.all().values('template_loc_tech', 'parameter', 'equation'))

    response = {
        #"model": model,
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
    POST: /templates/model/create
    """

    model_uuid = request.POST["model_uuid"]
    # technology_id = request.POST["technology_id"]
    # location_1_id = request.POST["location_1_id"]
    # location_2_id = request.POST.get("location_2_id", None)
    # loc_tech_description = request.POST.get("loc_tech_description", None)

    model = Model.by_uuid(model_uuid)
    model.handle_edit_access(request.user)

    # technology = model.technologies.filter(id=technology_id).first()
    # location_1 = model.locations.filter(id=location_1_id).first()
    # location_2 = model.locations.filter(id=location_2_id).first()
    # if technology.abstract_tech.name != "transmission":
    #     location_2_id = None

    # existing = model.loc_techs.filter(
    #     technology=technology,
    #     location_1=location_1,
    #     location_2=location_2,
    # )
    # if existing.first():
    #     loc_tech = existing.first()

    # else:
    #     loc_tech = Loc_Tech.objects.create(
    #         model=model,
    #         technology=technology,
    #         location_1=location_1,
    #         location_2=location_2,
    #         description=loc_tech_description,
    #     )
    # # Log Activity
    # comment = "{} added a node: {} ({}) @ {}.".format(
    #     request.user.get_full_name(),
    #     technology.pretty_name,
    #     technology.tag,
    #     location_1.pretty_name,
    # )
    # Model_Comment.objects.create(model=model, comment=comment, type="add")
    # model.notify_collaborators(request.user)

    # request.session["loc_tech_id"] = loc_tech.id
    payload = {"message": "added template to model",
            "template_id": 1}

    return HttpResponse(json.dumps(payload), content_type="application/json")