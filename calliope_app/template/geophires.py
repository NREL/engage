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
from taskmeta.models import CeleryTask
import matplotlib.pyplot as plt
from geophires.utils import fit_lower_bound
from template.models import Template_Type


logger = logging.getLogger(__name__)


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
        'power_plant_type': 1, #except if we add double flash = 4
        "number_of_segments": 4,

        # floats
        "reservoir_heat_capacity": float(formData["reservoir_heat_capacity"]),
        "reservoir_density": float(formData["reservoir_density"]),
        "reservoir_thermal_conductivity": float(formData["reservoir_thermal_conductivity"]),
        "min_reservoir_depth": float(formData["min_reservoir_depth"]),
        "max_reservoir_depth": float(formData["max_reservoir_depth"]),
        "gradient_1": float(formData["gradient_1"]),
        "gradient_2": float(formData["gradient_2"]),
        "gradient_3": float(formData["gradient_3"]),
        "gradient_4": float(formData["gradient_4"]), 
        "thickness_grad1": float(formData["thickness_grad1"]),
        "thickness_grad2": float(formData["thickness_grad2"]),
        "thickness_grad3": float(formData["thickness_grad3"]), 
        "well_drilling_cost_correlation": float(formData["well_drilling_cost_correlation"]),
        "target_prod_temp_min": float(formData["target_prod_temp_min"]),
        "target_prod_temp_max": float(formData["target_prod_temp_max"]),
        "production_well_diameter": float(formData["production_well_diameter"]),
        "injection_well_diameter": float(formData["injection_well_diameter"]),
        "lifetime": float(formData["lifetime"]),
        "interest_rate": float(formData["interest_rate"]),
        "electricity_rate": float(formData["electricity_rate"]), 

        # ints
        "min_production_wells": int(formData["min_production_wells"]), 
        "max_production_wells": int(formData["max_production_wells"]),
        "min_injection_wells": int(formData["min_injection_wells"]),
        "max_injection_wells": int(formData["max_injection_wells"]),
    }

    # Template based params
    if template_type.id == 1:
       # EGS_chp
        input_params["end_use_option"] = 31
        input_params["injection_temperature"] = 50
        input_params["reservoir_model"] = 3
        input_params["drawdown_parameter"] = float(0.00002)
        input_params["circulation_pump_efficiency"] = 0.80
        input_params["reservoir_volume_option"] = 1
        input_params["fracture_shape"] = float(formData["fracture_shape"])
        input_params["fracture_height"] = float(formData["fracture_height"])
        input_params["number_of_fractures"] = float(formData["number_of_fractures"])
    elif template_type.id == 2:
        # HYDRO_chp 
        input_params["end_use_option"] = 31
        input_params["injection_temperature"] = 50
        input_params["reservoir_model"] = 4
        input_params["drawdown_parameter"] = float(0.003)
        input_params["circulation_pump_efficiency"] = 0.80
        input_params["reservoir_volume_option"] = 1
        input_params['ramey_production_wellbore_model'] = 0
        input_params['production_wellbore_temperature_drop'] = 5
        input_params['injection_wellbore_temperature_gain'] = 3
        input_params['water_loss_fraction'] = 0.02
        input_params['injectivity_index'] = 5
        input_params["productivity_index"] = 10 # add in geophiresx
    if template_type.id == 3:
        # EGS_binary_orc
        input_params["end_use_option"] = 1
        input_params["injection_temperature"] = 70
        input_params["reservoir_model"] = 3
        input_params["drawdown_parameter"] = float(0.00002)
        input_params["circulation_pump_efficiency"] = 0.80
        input_params["reservoir_volume_option"] = 1
        input_params["fracture_shape"] = float(formData["fracture_shape"])
        input_params["fracture_height"] = float(formData["fracture_height"])
        input_params["number_of_fractures"] = float(formData["number_of_fractures"])
    if template_type.id == 4:
        # HYDRO_binary_orc
        input_params["end_use_option"] = 1
        input_params["injection_temperature"] = 70
        input_params["reservoir_model"] = 4
        input_params["drawdown_parameter"] = float(0.003)
        input_params["circulation_pump_efficiency"] = 0.80
        input_params["reservoir_volume_option"] = 4
        input_params['ramey_production_wellbore_model'] = 0
        input_params['production_wellbore_temperature_drop'] = 0
        input_params['injection_wellbore_temperature_gain'] = 0
        input_params['water_loss_fraction'] = 0.0
        input_params["injectivity_index"] = 10 
        input_params["productivity_index"] = 10 
        #input_params["ambient_temperature"] = 70 # defaulted
        #input_params["surface_temperature"] = 15 # defaulted
        #input_params["utilization_factor"] = .9 # defaulted
        #input_params["maximum_drawdown"] = 1 # defaulted
    elif template_type.id == 5:
        # HYDRO_cchp
        input_params["end_use_option"] = 31
        input_params["injection_temperature"] = 50
        input_params["reservoir_model"] = 3
        input_params["drawdown_parameter"] = float(0.003)
        input_params["circulation_pump_efficiency"] = 0.80
        input_params["reservoir_volume_option"] = 1
        input_params["fracture_shape"] = float(formData["fracture_shape"])
        input_params["fracture_height"] = float(formData["fracture_height"])
        input_params["number_of_fractures"] = float(formData["number_of_fractures"])
    elif template_type.id == 6:
        # EGS_cchp
        input_params["end_use_option"] = 31
        input_params["injection_temperature"] = 50
        input_params["reservoir_model"] = 4
        input_params["drawdown_parameter"] = float(0.00002)
        input_params["circulation_pump_efficiency"] = 0.80
        input_params["reservoir_volume_option"] = 1
        input_params['ramey_production_wellbore_model'] = 0
        input_params['production_wellbore_temperature_drop'] = 5
        input_params['injection_wellbore_temperature_gain'] = 3
        input_params['water_loss_fraction'] = 0.02
        input_params['injectivity_index'] = 5
    elif template_type.id == 7:
        # EGS_direct_use
        input_params["end_use_option"] = 2
        input_params["injection_temperature"] = 40
        input_params["reservoir_model"] = 3
        input_params["drawdown_parameter"] = float(0.003)
        input_params["circulation_pump_efficiency"] = 0.80
        input_params["reservoir_volume_option"] = 1
        input_params["ramey_production_wellbore_model"] = 1
        input_params["injection_wellbore_temperature_gain"] = 0
        input_params["fracture_seperation"] = 100 # new hardcoded?
        input_params["reservoir_impedance"] = 0.05 # new hardcoded?
        input_params["end-use_efficiency_factor"] = 0.9 # new hardcoded?
        input_params["ambient_temperature"] = 20 # hardcode? new param 
        input_params["surface_temperature"] = 20 # hardcode? new param 
        input_params["fracture_shape"] = float(formData["fracture_shape"])
        input_params["fracture_height"] = float(formData["fracture_height"])
        input_params["number_of_fractures"] = float(formData["number_of_fractures"])
        input_params["maximum_drawdown"] = float(0.3)
    elif template_type.id == 8:
        # HYDRO_direct_use
        input_params["end_use_option"] = 2
        input_params["injection_temperature"] = 40
        input_params["reservoir_model"] = 4
        input_params["drawdown_parameter"] = float(0.003)
        input_params["circulation_pump_efficiency"] = 0.80
        input_params["reservoir_volume_option"] = 1
        input_params["ramey_production_wellbore_model"] = 0
        input_params["production_wellbore_temperature_drop"] = 5
        input_params["injection_wellbore_temperature_gain"] = 3
        input_params["water_loss_fraction"] = 0.02
        input_params["injectivity_index"] = 5
        input_params["maximum_drawdown"] = 1

    # needs to know what the carrier is, all other values can be defaulted.
    if None in (
        input_params["end_use_option"],
        input_params["power_plant_type"]):
        raise ValidationError(f"Error: Required field not provided for GEOPHIRES.")

    try:
        job_input_params = input_params
        job_input_params["template_type"] = template_type.id
        job_meta = Job_Meta.objects.filter(inputs=job_input_params).first()
        if job_meta is None:
            payload["jobPreexisting"] = False
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
    template_type = Template_Type.objects.filter(id=job_meta.inputs["template_type"]).first()

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
    #heating_capacity = safe_extract(df, 'Average Heat Production (MWth)')
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
    note = "Best fit to least cost, the slope indicates the $/KWe<br>"

    # Plot1
    x1 = electric_capacity
    y1 = surface_cost
    a1, b1, x1_line, lower_b1_line, label_b1 = fit_lower_bound(x1, y1,1)         # electric cap vs surface cost
    b1_values       = y1 - np.multiply(a1, x1)
    # Change this line to fit_lower_bound
    label_b1        = f"y={a1:.4f}x+{np.min(b1_values):.4f}" if np.min(b1_values) > 0 else f"y={a1:.4f}x{np.min(b1_values):.4f}"
    label_b1        = f"<br><br><span>{label_b1}</span><br><span style='font-size: 9px'>{note}</span>"

    # Plot2
    x2              = electric_capacity
    y2              = surface_o_m_cost
    a2, b2, x2_line, lower_b2_line, label_b2 = fit_lower_bound(x2, y2,1) 
    b2_values       = y2 - np.multiply(a2, x2)
    # Change this line to fit_lower_bound
    label_b2        = f"y={a2:.4f}x+{np.min(b2_values):.4f}" if np.min(b2_values) > 0 else f"y={a2:.4f}x{np.min(b2_values):.4f}"
    label_b2        = f"<br><br><span>{label_b2}</span><br><span style='font-size: 9px'>{note}</span>"

    # Plot3
    x3              = thermal_capacity
    y3              = reservoir_cost
    a3, b3, x3_line, lower_b3_line, label_b3 = fit_lower_bound(x3, y3, 1) 
    b3_values       = y3 - np.multiply(a3, x3)
    label_b3        = f"y={a3:.4f}x+{np.min(b3_values):.4f}" if np.min(b3_values) > 0 else f"y={a3:.4f}x{np.min(b3_values):.4f}"
    label_b3        = f"<br><br><span>{label_b3}</span><br><span style='font-size: 9px'>{note}</span>"

    # Plot4
    x4              = thermal_capacity
    y4              = reservoir_o_m_cost
    a4, b4, x4_line, lower_b4_line, label_b4 = fit_lower_bound(x4, y4, 1) 
    b4_values       = y4 - np.multiply(a4, x4)
    # Fit Lower. 
    label_b4        = f"y={a4:.4f}x+{np.min(b4_values):.4f}" if np.min(b4_values) > 0 else f"y={a4:.4f}x{np.min(b4_values):.4f}"
    label_b4        = f"<br><br><span>{label_b4}</span><br><span style='font-size: 9px'>{note}</span>"
    
    # Reservoir

    outputs = {
        "params": output_params,
        "pwells": [int(i) for i in  electric_capacity],
        "temperature": unique_temp.tolist(),
        "template_type": template_type.pretty_name,
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
