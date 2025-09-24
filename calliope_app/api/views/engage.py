import json

from django.http import HttpResponse
from django.views.decorators.csrf import csrf_protect

from api.tasks import upgrade_066, upgrade_070_flow_cap_carriers, update_scenario_math_params

from api.models.configuration import Model


@csrf_protect
def apply_upgrade_066(request):
    """
    Launch data migration to Calliope 066.

    Parameters:

    Returns (json): Action Confirmation

    Example:
    POST: /api/upgrade_066/
    """

    payload = {}
    if request.user.is_staff:
        async_result = upgrade_066.apply_async()
        payload['task_id'] = async_result.id
    else:
        payload['message'] = "Not authorized!"

    return HttpResponse(json.dumps(payload), content_type="application/json")

@csrf_protect
def apply_upgrade_070_flow_cap_carriers(request):
    """
    Launch data migration to Calliope 066.

    Parameters:

    Returns (json): Action Confirmation

    Example:
    POST: /api/upgrade_070_flow_cap_carriers/
    """
    payload = {}
    if request.user.is_staff:
        async_result = upgrade_070_flow_cap_carriers.apply_async()
        payload['task_id'] = async_result.id
    else:
        payload['message'] = "Not authorized!"

    return HttpResponse(json.dumps(payload), content_type="application/json")

@csrf_protect
def apply_update_scenario_math_params(request):
    """
    Launch data migration to Calliope 066.

    Parameters:

    Returns (json): Action Confirmation

    Example:
    POST: /api/update_scenario_math_params/
    """
    model_uuid = request.POST["model_uuid"]
    model = Model.by_uuid(model_uuid)
    model.handle_edit_access(request.user)
    scenario_id = request.POST["scenario_id"]
    payload = {}
    async_result = update_scenario_math_params.apply_async(
            kwargs={
                "scenario_id": scenario_id
                })
    payload['task_id'] = async_result.id
    
    return HttpResponse(json.dumps(payload), content_type="application/json")
