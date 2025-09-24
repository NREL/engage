import json

from django.http import HttpResponse
from django.views.decorators.csrf import csrf_protect

from api.tasks import upgrade_066, upgrade_070_flow_cap_carriers, update_scenario_math_params, update_supply_cost_in

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
    flow_cap is now per-carrier. Update all flow_cap related params to be indexed on carrier.

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
    Refresh the scenario parameters to (potentially new) defaults.
    Useful for picking up custom math updates.

    Parameters:

    model_uuid: Model id
    scenario_id: Scenario id

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

@csrf_protect
def apply_update_supply_cost_in(request):
    """
    We are now using cost_source_use instead of cost_flow_in for supply.
    Update all supply cost_flow_in params to be cost_source_use.

    Parameters:

    Returns (json): Action Confirmation

    Example:
    POST: /api/apply_update_supply_cost_in/
    """
    payload = {}
    if request.user.is_staff:
        async_result = update_supply_cost_in.apply_async()
        payload['task_id'] = async_result.id
    else:
        payload['message'] = "Not authorized!"

    return HttpResponse(json.dumps(payload), content_type="application/json")
