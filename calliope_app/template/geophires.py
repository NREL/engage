import json
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_protect
from django.core.exceptions import ValidationError
from django.http import HttpResponse
from api.utils import initialize_units, convert_units_no_pipe

@login_required
@csrf_protect
def request_geophires(request):
    """
    Parameters:
    location: required(?)
    reservoir_heat_capacity: required
    reservoir_density: required 
    reservoir_thermal_conductivity: required
    gradient: required
    min_temperature: required
    max_temperature: required
    min_reservoir_depth: required
    max_reservoir_depth: required
    min_production_wells: required
    max_production_wells: required
    min_injection_wells: required
    max_injection_wells: required

    Returns (json): Action Confirmation

    Example:
    POST: /geophires/
    """
    location_id = request.POST["location"]
    formData = json.loads(request.POST["form_data"])
    print(formData)

    if None in (location_id, formData["reservoir_heat_capacity"], formData["reservoir_density"], formData["reservoir_thermal_conductivity"], formData["gradient"],
        formData["min_temperature"], formData["max_temperature"], formData["min_reservoir_depth"], formData["max_reservoir_depth"], formData["min_production_wells"],
        formData["max_production_wells"], formData["min_injection_wells"], formData["max_injection_wells"]):
        raise ValidationError(f"Error: Required field not provided for GEOPHIRES.")
    

    payload = {"message": "ran geophires",
                }

    return HttpResponse(json.dumps(payload), content_type="application/json")