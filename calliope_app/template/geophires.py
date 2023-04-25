import json
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_protect
from django.core.exceptions import ValidationError
from django.http import HttpResponse
from api.utils import initialize_units, convert_units_no_pipe
from api.models.configuration import Job_Meta

@login_required
@csrf_protect
def geophires_response(request):
    """
    Parameters:
    job_meta_id: required

    Returns (json): Action Confirmation

    Example:
    POST: /geophires/response
    """
    #return information to plot graphs and map to geophires outputs
    responseData = {"status": "complete"}
    return HttpResponse(json.dumps({responseData}), content_type="application/json")

@login_required
@csrf_protect
def geophires_request_status(request):
    """
    Parameters:
    job_meta_id: required

    Returns (json): Action Confirmation

    Example:
    POST: /geophires/status
    """
    job_meta_id = request.POST["job_meta_id"]
    job_meta = Job_Meta.objects.filter(id=job_meta_id).first()
    return HttpResponse(json.dumps(job_meta), content_type="application/json")


@login_required
@csrf_protect
def geophires_request(request):
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

    payload = {"message": "starting runnning geophires"}

    #seralize data
    inputs = {
        "reservoir_heat_capacity": formData["reservoir_heat_capacity"],
        "reservoir_density": formData["reservoir_density"],
        "reservoir_thermal_conductivity": formData["reservoir_thermal_conductivity"],
        "gradient": formData["gradient"],
        "min_temperature": formData["min_temperature"],
        "max_temperature": formData["max_temperature"],
        "min_reservoir_depth": formData["min_reservoir_depth"],
        "max_reservoir_depth": formData["max_reservoir_depth"],
        "min_production_wells": formData["min_production_wells"],
        "max_production_wells": formData["max_production_wells"],
        "min_injection_wells": formData["min_injection_wells"],
    }

    if None in (location_id, formData["reservoir_heat_capacity"], formData["reservoir_density"], formData["reservoir_thermal_conductivity"], formData["gradient"],
        formData["min_temperature"], formData["max_temperature"], formData["min_reservoir_depth"], formData["max_reservoir_depth"], formData["min_production_wells"],
        formData["max_production_wells"], formData["min_injection_wells"], formData["max_injection_wells"]):
        raise ValidationError(f"Error: Required field not provided for GEOPHIRES.")

    job_meta = Job_Meta.objects.filter(inputs=inputs).first()
    if job_meta is None:
        payload.jobPreexisting = False
        print("new process started")
        #1. QUEUED = "QUEUED"
        #2. RUNNING = "RUNNING"
        #3. SUCCESS = "SUCCESS”/FAILURE = "FAILURE"

        #Set output_path?
        job_meta = Job_Meta.objects.create(inputs=inputs, status="QUEUED", type="geophires")
        # if it doesn't exist create one and start celery process
        # call a new function in tasks.py with apply_async
        # Goes into RUNNING status after that and job_task is set from the celery process
    else:
        payload.jobPreexisting = True

    payload.job_meta_id = job_meta.id
    payload.job_status = job_meta.status


    return HttpResponse(json.dumps(payload), content_type="application/json")