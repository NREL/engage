import json
import logging

from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_protect
from django.core.exceptions import ValidationError
from django.http import HttpResponse

from api.models.configuration import Job_Meta
from geophires.tasks import run_geophires
from taskmeta.models import CeleryTask

logger = logging.getLogger(__name__)


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
    if job_meta:
        job_meta_dict = {
            "type": job_meta.type,
            "inputs": job_meta.inputs,
            "outputs": job_meta.outputs,
            "status": job_meta.status
        }
    else:
        job_meta_dict = {}
    return HttpResponse(json.dumps(job_meta_dict), content_type="application/json")


@login_required
@csrf_protect
def geophires_request(request):
    """
    Parameters:
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
    formData = json.loads(request.POST["form_data"])

    payload = {"message": "starting runnning geophires"}

    #seralize data
    input_params = {
        "reservoir_heat_capacity": float(formData["reservoir_heat_capacity"]),
        "reservoir_density": float(formData["reservoir_density"]),
        "reservoir_thermal_conductivity": float(formData["reservoir_thermal_conductivity"]),
        "gradient": float(formData["gradient"]),
        
        # TODO: Step sizes are hardcoded, need to refactor later
        "min_temperature": float(formData["min_temperature"]),
        "max_temperature": float(formData["max_temperature"]),
        "temperature_step": 25.0,
        
        "min_reservoir_depth": float(formData["min_reservoir_depth"]),
        "max_reservoir_depth": float(formData["max_reservoir_depth"]),
        "reservoir_depth_step": 0.1,

        "min_production_wells": int(formData["min_production_wells"]),
        "max_production_wells": int(formData["max_production_wells"]),
        "production_wells_step": 1,
        
        "min_injection_wells": int(formData["min_injection_wells"]),
        "max_injection_wells": int(formData["max_injection_wells"]),
        "injection_wells_step": 1
    }

    if None in (formData["reservoir_heat_capacity"], formData["reservoir_density"], formData["reservoir_thermal_conductivity"], formData["gradient"],
        formData["min_temperature"], formData["max_temperature"], formData["min_reservoir_depth"], formData["max_reservoir_depth"], formData["min_production_wells"],
        formData["max_production_wells"], formData["min_injection_wells"], formData["max_injection_wells"]):
        raise ValidationError(f"Error: Required field not provided for GEOPHIRES.")

    try:
        inputs = {
            "input_plant": "binary_subcritical",
            "input_params": input_params
        }
        job_meta = Job_Meta.objects.filter(inputs=inputs).first()
        if job_meta is None:
            payload["jobPreexisting"] = False
            job_meta = Job_Meta.objects.create(inputs=inputs, status="QUEUED", type="geophires")
            async_result = run_geophires.apply_async(
                kwargs={
                    "job_meta_id": job_meta.id,
                    "plant": inputs["input_plant"],
                    "params": inputs["input_params"],
                }
            )
            celery_task = CeleryTask.objects.get(task_id=async_result.id)
            job_meta.job_task = celery_task
            job_meta.save()
            logger.info("Geophires task %s starts to run in celery worker.", job_meta.id)
        
        else:
            payload["jobPreexisting"] = True

        payload.update({
            "job_meta_status": job_meta.status,
            "job_meta_id": job_meta.id,
        })
    
    except Exception as e:
        logger.exception(e)
        payload = {
            "status": "Failed",
            "message": "Failed to run geophires task, please reconfig and try again. ' \
                'If any concerns, please contact admin at engage@nrel.gov ' \
                'regarding this error: {}".format(str(e)),
        }
    
    return HttpResponse(json.dumps(payload), content_type="application/json")
