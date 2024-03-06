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
from template.models import Template_Type


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
    Returns (json): Action Confirmation

    Example:
    POST: /geophires/
    """
    formData = json.loads(request.POST["form_data"])
    template_type = Template_Type.objects.filter(id=formData["templateType"]).first()
    payload = {"message": "starting runnning geophires"}
    input_params = {
        # hardcoded
        "max_temperature": 400,
        "print_output_to_console": 0,

        # floats
        "reservoir_heat_capacity": float(formData["reservoir_heat_capacity"]),
        "reservoir_density": float(formData["reservoir_density"]),
        "reservoir_thermal_conductivity": float(formData["reservoir_thermal_conductivity"]),
        "min_reservoir_depth": float(formData["min_reservoir_depth"]),
        "max_reservoir_depth": float(formData["max_reservoir_depth"]),
        "number_of_segments": int(float(formData["number_of_segments"])),
        "gradient_1": float(formData["gradient_1"]),
        "gradient_2": float(formData["gradient_2"]),
        "gradient_3": float(formData["gradient_3"]),
        "gradient_4": float(formData["gradient_4"]),
        "fracture_shape": float(formData["fracture_shape"]),
        "fracture_height": float(formData["fracture_height"]),
        "number_of_fractures": float(formData["number_of_fractures"]),
        "well_drilling_cost_correlation": float(formData["well_drilling_cost_correlation"]),
        "target_prod_temp_min": float(formData["target_prod_temp_min"]),
        "target_prod_temp_max": float(formData["target_prod_temp_max"]),
        "lifetime": float(formData["lifetime"]),
        "production_well_diameter": float(formData["production_well_diameter"]),
        "injection_well_diameter": float(formData["injection_well_diameter"]),

        # ints
        "min_production_wells": int(formData["min_production_wells"]),
        "max_production_wells": int(formData["max_production_wells"]),
        "min_injection_wells": float(formData["min_injection_wells"]),
        "max_injection_wells": float(formData["max_injection_wells"]),
    }

    # Template based params
    if template_type and template_type.id == 1:
        input_params["end_use_option"] = 31
        input_params["injection_temperature"] = 50
        input_params["reservoir_model"] = 3
        input_params["drawdown_parameter"] = 0.00002
        input_params["circulation_pump_efficiency"] = 0.80
        input_params["reservoir_volume_option"] = 1
        input_params["power_plant_type"] = 1

    if None in (formData["reservoir_heat_capacity"],
        input_params["reservoir_density"],
        input_params["reservoir_thermal_conductivity"],
        input_params["min_reservoir_depth"], 
        input_params["max_reservoir_depth"], 
        input_params["number_of_segments"], 
        input_params["gradient_1"],
        input_params["gradient_2"],
        input_params["gradient_3"],
        input_params["gradient_4"],
        input_params["fracture_shape"],
        input_params["fracture_height"],
        input_params["number_of_fractures"],
        input_params["well_drilling_cost_correlation"],
        input_params["target_prod_temp_min"],
        input_params["target_prod_temp_max"],  
        input_params["lifetime"],   
        input_params["production_well_diameter"],   
        input_params["injection_well_diameter"],     
        input_params["min_production_wells"],
        input_params["max_production_wells"], 
        input_params["min_injection_wells"], 
        input_params["max_injection_wells"],
        input_params["end_use_option"],
        input_params["injection_temperature"],
        input_params["reservoir_model"],
        input_params["drawdown_parameter"],
        input_params["circulation_pump_efficiency"],
        input_params["reservoir_volume_option"],
        input_params["power_plant_type"]):
        raise ValidationError(f"Error: Required field not provided for GEOPHIRES.")

    try:
        job_meta = Job_Meta.objects.filter(inputs=input_params).first()
        if job_meta is None:
            payload["jobPreexisting"] = False
            job_input_params = input_params
            job_input_params["template_type"] = template_type.id
            job_meta = Job_Meta.objects.create(inputs=job_input_params, status=task_status.RUNNING, type="geophires")
            async_result = run_geophires.apply_async(
                kwargs={
                    "job_meta_id": job_meta.id,
                    "params": input_params,
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

    output_params = job_meta.outputs["output_params"]
    output_file = job_meta.outputs["output_file"]

    df = pd.read_csv(output_file)
    logger.info(f"\n\n\n ------- Read DF ------ \n\n\n")
    

    # TODO update outputs to be these, np.array() for all of them?
    # max_elec_gen
    # elec_cap_vs_surface_cost
    # elec_cap_vs_surface_o&m_cost
    # max_avg_therm_ext
    # therm_cap_vs_reservoir_cost
    # therm_cap_vs_reservoir_om_cost
    # elec_prod_to_therm_ext_ratio
    # heat_prod_to_therm_ext_ratio
    # therm_ext_to_therm_ext_ratio
    
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
    # a1, b1          = popt
    # x1_line         = np.asarray([np.min(x1), np.max(x1)])
    a1, b1, x1_line, lower_b1_line, label_b1 = fit_lower_bound(x1, y1,1)         # electric cap vs surface cost
    b1_values       = y1 - np.multiply(a1, x1)
    # Change this line to fit_lower_bound
    label_b1        = f"y={a1:.4f}x+{np.min(b1_values):.4f}" if np.min(b1_values) > 0 else f"y={a1:.4f}x{np.min(b1_values):.4f}"
    label_b1        = f"<br><br><span>{label_b1}</span><br><span style='font-size: 9px'>{note}</span>"

    # Plot2
    x2              = electric_capacity
    y2              = surface_o_m_cost
    # popt, _         = curve_fit(objective, x2, y2)
    # a2, b2          = popt
    # x2_line         = np.asarray([np.min(x2), np.max(x2)])
    a2, b2, x2_line, lower_b2_line, label_b2 = fit_lower_bound(x2, y2,1) 
    b2_values       = y2 - np.multiply(a2, x2)
    # Change this line to fit_lower_bound
    label_b2        = f"y={a2:.4f}x+{np.min(b2_values):.4f}" if np.min(b2_values) > 0 else f"y={a2:.4f}x{np.min(b2_values):.4f}"
    label_b2        = f"<br><br><span>{label_b2}</span><br><span style='font-size: 9px'>{note}</span>"

    # Plot3
    x3              = thermal_capacity
    y3              = reservoir_cost
    # popt, _         = curve_fit(objective, x3, y3)
    # a3, b3         = popt
    # Change this line to fit_lower_bound
    # x3_line         = np.asarray([np.min(x3), np.max(x3)])
    a3, b3, x3_line, lower_b3_line, label_b3 = fit_linear_model(x3, y3,3,0.3,0) 
    b3_values       = y3 - np.multiply(a3, x3)
    label_b3        = f"y={a3:.4f}x+{np.min(b3_values):.4f}" if np.min(b3_values) > 0 else f"y={a3:.4f}x{np.min(b3_values):.4f}"
    label_b3        = f"<br><br><span>{label_b3}</span><br><span style='font-size: 9px'>{note}</span>"

    # Plot4
    x4              = thermal_capacity
    y4              = reservoir_o_m_cost
    popt, _         = curve_fit(objective, x4, y4)
    # a4, b4         = popt
    # x4_line         = np.asarray([np.min(x4), np.max(x4)])
    a4, b4, x4_line, lower_b4_line, label_b4 = fit_lower_bound(x4, y4,1) 
    b4_values       = y4 - np.multiply(a4, x4)

    # Change this line to fit_linear_model. 
    label_b4        = f"y={a4:.4f}x+{np.min(b4_values):.4f}" if np.min(b4_values) > 0 else f"y={a4:.4f}x{np.min(b4_values):.4f}"
    label_b4        = f"<br><br><span>{label_b4}</span><br><span style='font-size: 9px'>{note}</span>"
    a4, b4, x4_line, lower_b4_line, label_b4 = fit_lower_bound(thermal_capacity, reservoir_o_m_cost,0)    # thermal cap vs reservoir O&M cost
    
    # Reservoir

    outputs = {
        "params": output_params,
        "pwells": [int(i) for i in  electric_capacity],
        "temperature": unique_temp.tolist(),

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
