from pytz import common_timezones

from django.conf import settings
from django.shortcuts import render
from django.contrib.auth.decorators import login_required

from api.models.configuration import Model, Model_User
from template.models import Template_Types

@login_required
def templates_admin_view(request):
    """
    Get "Templates" data

    Returns: HttpResponse

    Example:
    GET: /template/admin/
    """
    
    model_uuid = request.GET['model_uuid']
    model = Model.by_uuid(model_uuid)
    
    user_models = Model_User.objects.filter(
        user=request.user,
        model__snapshot_version=None,
        model__public=False).order_by('-last_access')
    model_ids = user_models.values_list(
        "model_id", flat=True)
    snapshots = Model.objects.filter(
        snapshot_base_id__in=model_ids)
    public_models = Model.objects.filter(
        snapshot_version=None,
        public=True)
    user_models = list(user_models)
    #template_models = Template_Type.objects

    if len(user_models) > 0:
        last_model = user_models[0].model
    elif len(public_models) > 0:
        last_model = public_models[0]
    else:
        last_model = None

    response = {
        "timezones": common_timezones,
        "last_model": last_model,
        "user_models": user_models,
        "public_models": public_models,
        "snapshots": snapshots,
        "mapbox_token": settings.MAPBOX_TOKEN,
        #"template_models": template_models,
        "model": model,
    }

    response = {
        "carriers": model.carriers
    }

    return JsonResponse(response, safe=False)
