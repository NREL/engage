import json
import logging

import numpy as np
import pandas as pd

from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_protect
from django.core.exceptions import ValidationError
from django.http import HttpResponse
from django.shortcuts import render

from api.models.configuration import Job_Meta
from geophires.tasks import run_geophires, task_status
# from geophires.geophiresx import Geophires
from geophires.geophiresx import objective
from scipy.optimize import curve_fit
from taskmeta.models import CeleryTask
from geophires_x_client import GeophiresXClient
import matplotlib.pyplot as plt
from geophires.utils import fit_linear_model, fit_lower_bound
logger = logging.getLogger(__name__)


def map_params(formData, geo_technology):
    if geo_technology.lower() == "egs_chp":
        return {
            "reservoir_heat_capacity": 1,
            "reservoir_density": 1,
            "reservoir_thermal_conductivity": 1,
            "min_reservoir_depth": 1,
            "max_reservoir_depth": 1,
            "min_production_wells": 1,
            "max_production_wells": 1,
            "min_injection_wells": 1,
            "max_injection_wells": 1,
            "Number_of_segments": 1,
            "Gradient_1": 1,
            "Gradient_2": 1,
            "Gradient_3": 1,
            "Gradient_4": 1,
            "Fracture_Shape": 1,
            "Fracture_Height": 1,  
            "Number_of_Fractures": 1,
            "Well_Drilling_Cost_Correlation": 1,
            "target_prod_temp_min": 1,
            "target_prod_temp_max": 1,
            "lifetime": 1,
            "thickness_grad1": 1,
            "thickness_grad2": 1,
            "thickness_grad3": format(formData["thickness 3"]),
    }

# Function to safely extract a column as an array, or fill with zeros if not present
def safe_extract(df, column_name):
    if column_name in df.columns:
        return np.array(df[column_name])
    else:
        print(f"'{column_name}' not found in DataFrame. Filling with zeros.")
        return np.zeros(len(df))

# Function to check if data is all zeros or empty
def has_data(*args):
    return all(not np.all(arg == 0) and len(arg) > 0 for arg in args)


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
    return HttpResponse(json.dumps(responseData), content_type="application/json")


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
    # We need to change how these valus are stored based on the new forms data. 
    input_params = {
        "reservoir_heat_capacity": float(formData["reservoir_heat_capacity"]),
        "reservoir_density": float(formData["reservoir_density"]),
        "reservoir_thermal_conductivity": float(formData["reservoir_thermal_conductivity"]),
        "gradient": float(formData["gradient"]),

        # TODO: Step sizes are hardcoded, need to refactor later
        "min_temperature": 400,
        "max_temperature": 400,
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
        formData["min_reservoir_depth"], formData["max_reservoir_depth"], formData["min_production_wells"],
        formData["max_production_wells"], formData["min_injection_wells"], formData["max_injection_wells"]):
        raise ValidationError(f"Error: Required field not provided for GEOPHIRES.")

    try:
        inputs = {
            "input_plant": "binary_subcritical",
            "input_params": input_params
        }
        job_meta = Job_Meta.objects.filter(inputs=inputs).first()
        logger.info(f"\n\n\n\n\n\n\n\n\n\n\n")
        logger.info(job_meta is None)
        logger.info(f"\n\n\n\n\n\n\n\n\n\n\n")

        if job_meta is None:
            payload["jobPreexisting"] = False
            logger.info(f"Entered!!!!!!!!!")

            job_meta = Job_Meta.objects.create(inputs=inputs, status=task_status.RUNNING, type="geophires")
            # Run geophiresx version instead
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
            "id": job_meta.id,
            "type": job_meta.type,
            "inputs": job_meta.inputs,
            "outputs": job_meta.outputs,
            "status": job_meta.status
        })

    except Exception as e:
        logger.exception(e)
        payload = {
            "status": "FAILURE",
            "message": "Failed to run geophires task, please reconfig and try again. ' \
                'If any concerns, please contact admin at engage@nrel.gov ' \
                'regarding this error: {}".format(str(e)),
        }

    return HttpResponse(json.dumps(payload), content_type="application/json")


@login_required
@csrf_protect
def geophires_outputs(request):
    """geophires outputs API function

    Parameters
    ----------
    id : str

    Returns
    -------
    HttpResponse (json)

    Examples
    --------
    GET: /geophires/outputs/?id=
    """
    job_meta_id = request.GET.get('id')
    job_meta = Job_Meta.objects.get(id=job_meta_id)

    plant = job_meta.outputs["plant"]
    output_params = job_meta.outputs["output_params"]
    output_file = job_meta.outputs["output_file"]

    df = pd.read_csv(output_file)
    logger.info(f"\n\n\n ------- Read DF ------ \n\n\n")
    

    # Prepare data for plots
    cmap = plt.get_cmap('plasma')
    unique_prod_wells = df['Number of Prod Wells'].unique()
    unique_inj_wells = df['Number of Inj Wells'].unique()
    unique_depth = df['Depth (km)'].unique()
    unique_temp = df['Average Production Temperature (degC)'].unique()

    # Safe extraction of columns
    heating_capacity = safe_extract(df, 'Average Heat Production (MWth)')
    electric_capacity = safe_extract(df, 'Average Electricity Production (MWe)')
    surface_cost = safe_extract(df, 'Surface Plant Cost ($M)')
    surface_o_m_cost = safe_extract(df, 'Surface maintenance costs ($MUSD/yr)')
    # eff = safe_extract(df_final, 'Eff ($MUSD/yr)')

    # Reservoir related data
    thermal_capacity = safe_extract(df, 'Average Reservoir Heat Extraction (MWth)')
    reservoir_cost = safe_extract(df, 'Drilling and completion cost ($MUSD)')
    reservoir_o_m_cost = safe_extract(df, 'Wellfield maintenance costs ($MUSD/yr)') + safe_extract(
        df, 'Make-Up Water O&M Cost ($MUSD/year)'
    )

    # Label notes
    note = "Best fit to least cost, the slope indicates the $/MW<br>"

    # Plot1
    x1 = electric_capacity
    y1 = surface_cost
    popt, _         = curve_fit(objective, x1, y1)
    a1, b1          = popt
    x1_line         = np.asarray([np.min(x1), np.max(x1)])
    b1_values       = y1 - np.multiply(a1, x1)
    # Change this line to fit_lower_bound
    lower_b1_line   = objective(x1_line, a1, np.min(b1_values))
    label_b1        = f"y={a1:.4f}x+{np.min(b1_values):.4f}" if np.min(b1_values) > 0 else f"y={a1:.4f}x{np.min(b1_values):.4f}"
    label_b1        = f"<br><br><span>{label_b1}</span><br><span style='font-size: 9px'>{note}</span>"

    # Plot2
    x2              = electric_capacity
    y2              = surface_o_m_cost
    popt, _         = curve_fit(objective, x2, y2)
    a2, b2          = popt
    x2_line         = np.asarray([np.min(x2), np.max(x2)])
    b2_values       = y2 - np.multiply(a2, x2)
    # Change this line to fit_lower_bound
    lower_b2_line   = objective(x2_line, a2, np.min(b2_values))
    label_b2        = f"y={a2:.4f}x+{np.min(b2_values):.4f}" if np.min(b2_values) > 0 else f"y={a2:.4f}x{np.min(b2_values):.4f}"
    label_b2        = f"<br><br><span>{label_b2}</span><br><span style='font-size: 9px'>{note}</span>"

    # Plot3
    x3              = thermal_capacity
    y3              = reservoir_cost
    popt, _         = curve_fit(objective, x3, y3)
    a3, b3         = popt
    # Change this line to fit_lower_bound
    x3_line         = np.asarray([np.min(x3), np.max(x3)])
    b3_values       = y3 - np.multiply(a3, x3)
    lower_b3_line   = objective(x3_line, a3, np.min(b3_values))
    label_b3        = f"y={a3:.4f}x+{np.min(b3_values):.4f}" if np.min(b3_values) > 0 else f"y={a3:.4f}x{np.min(b3_values):.4f}"
    label_b3        = f"<br><br><span>{label_b3}</span><br><span style='font-size: 9px'>{note}</span>"

    # Plot4
    x4              = thermal_capacity
    y4              = reservoir_o_m_cost
    popt, _         = curve_fit(objective, x4, y4)
    a4, b4         = popt
    x4_line         = np.asarray([np.min(x4), np.max(x4)])
    b4_values       = y4 - np.multiply(a4, x4)
    # Change this line to fit_linear_model. 
    lower_b4_line   = objective(x4_line, a4, np.min(b4_values))
    label_b4        = f"y={a4:.4f}x+{np.min(b4_values):.4f}" if np.min(b4_values) > 0 else f"y={a4:.4f}x{np.min(b4_values):.4f}"
    label_b4        = f"<br><br><span>{label_b4}</span><br><span style='font-size: 9px'>{note}</span>"

    pretty_plant = plant.replace("_", " ").title()
    outputs = {
        "plant": pretty_plant,
        "params": output_params,
        "pwells": [int(i) for i in  electric_capacity],
        "depths": surface_cost.tolist(),

        "plot1": {
            "x1": x1.tolist(),
            "y1": y1.tolist(),
            "x1_line": x1_line.tolist(),
            "lower_b1_line": lower_b1_line.tolist(),
            "label_b1": label_b1
        },
        "plot2": {
            "x2": x2.tolist(),
            "y2": y2.tolist(),
            "x2_line": x2_line.tolist(),
            "lower_b2_line": lower_b2_line.tolist(),
            "label_b2": label_b2
        },
        "plot3": {
            "x3": x3.tolist(),
            "y3": y3.tolist(),
            "x3_line": x3_line.tolist(),
            "lower_b3_line": lower_b3_line.tolist(),
            "label_b3": label_b3
        },
        "plot4": {
            "x4": x4.tolist(),
            "y4": y4.tolist(),
            "x4_line": x4_line.tolist(),
            "lower_b4_line": lower_b4_line.tolist(),
            "label_b4": label_b4
        }
    }

    return HttpResponse(json.dumps(outputs), content_type="application/json")


@login_required
@csrf_protect
def geophires_plotting(request):
    """geophires plotting view function

    Parameters
    ----------
    id : str

    Returns
    -------
    HttpResponse

    Examples
    --------
    GET: /geophires/plotting/?id=
    """
    job_meta_id = request.GET.get('id')
    try:
        job_meta = Job_Meta.objects.get(id=job_meta_id)
        context = {
            "job_meta_id": job_meta.id
        }
    except Job_Meta.DoesNotExist:
        context = {
            "job_meta_id": None
        }

    return render(request, "geophires_plotting.html", context)
