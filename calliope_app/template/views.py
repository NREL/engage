from pytz import common_timezones
from django.conf import settings
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_protect
from django.http import JsonResponse
from api.models.configuration import Model, Model_User
from template.models import Template_Types

@login_required
@csrf_protect
def templates_admin_view(request):
    """
    Get "Templates" data

    Returns: JsonResponse

    Example:
    GET: /templates/admin/
    """
    
    model_uuid = request.GET['model_uuid']
    #model = Model.by_uuid(model_uuid)
    
    template_types = Template_Types.objects.get()
    #template_types = Template_Types.all()
    #template_types = Loc_Tech.objects.get(id=loc_tech_id)
    #template_types = ["HI"]

    response = {
        #"model": model,
        "template_types": template_types,
    }

    return JsonResponse(response, safe=False)

