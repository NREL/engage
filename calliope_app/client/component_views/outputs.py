from django.http import HttpResponse, JsonResponse, Http404
from django.shortcuts import render
from django.views.decorators.csrf import csrf_protect
from django.utils.html import mark_safe
from django.conf import settings

from api.models.configuration import Model
from api.models.outputs import Run, Cambium
from api.tasks import task_status

import os
import io
import json
from datetime import datetime
import pandas as pd
from collections import defaultdict


@csrf_protect
def run_dashboard(request):
    """
    Retrieve the runs for a scenario

    Parameters:
    model_uuid (uuid): required
    scenario_id (int): optional

    Returns: HttpResponse

    Example:
    POST: /component/run_dashboard/
    """

    model_uuid = request.POST['model_uuid']
    scenario_id = request.POST.get('scenario_id', None)
    if scenario_id is not None:
        request.session['scenario_id'] = scenario_id

    model = Model.by_uuid(model_uuid)
    can_edit = model.handle_view_access(request.user)

    runs = model.runs.filter(scenario_id=scenario_id)

    for run in runs:
        run.run_options = json.dumps(run.run_options)
        
    # Check for any publication updates
    for run in runs.filter(published=None):
        Cambium.push_run(run)

    context = {
        "model": model,
        "runs": runs,
        "can_edit": can_edit,
        "task_status": task_status,
        "cambium_configured": bool(settings.CAMBIUM_API_KEY)
    }
    html = list(render(request, 'run_dashboard.html', context))[0]

    payload = {
        'html': html.decode('utf-8')}

    return HttpResponse(json.dumps(payload), content_type="application/json")


@csrf_protect
def add_run_precheck(request):
    """
    Retrieve the precheck for a new scenario run

    Parameters:
    model_uuid (uuid): required
    scenario_id (int): required

    Returns: HttpResponse

    Example:
    GET: /component/add_run_precheck/
    """

    model_uuid = request.GET['model_uuid']
    scenario_id = request.GET['scenario_id']

    model = Model.by_uuid(model_uuid)
    can_edit = model.handle_view_access(request.user)

    scenario = model.scenarios.filter(id=scenario_id).first()

    runs = model.runs.filter(scenario=scenario)
    runs = runs.order_by('-created')
    prev_dates = []
    for run in runs:
        start_date, end_date = run.subset_time.split(' to ')
        s_date = datetime.strptime(start_date, '%Y-%m-%d')
        e_date = datetime.strptime(end_date, '%Y-%m-%d')
        n_days = (e_date - s_date).days + 1
        days = '&nbsp;&nbsp;&nbsp;(' + str(n_days) + ' days)'
        s_date = '<b>' + s_date.strftime('%b. %-d, %Y') + '</b>'
        e_date = '<b>' + e_date.strftime('%b. %-d, %Y') + '</b>'
        formatted = s_date + '&nbsp;&nbsp;to&nbsp;&nbsp;' + e_date + days
        prev_date = (start_date, end_date, mark_safe(formatted))
        if prev_date not in prev_dates:
            prev_dates.append(prev_date)

    timeseries, missing_timeseries = scenario.timeseries_precheck()

    context = {
        "prev_dates": prev_dates[:4],
        "model": model,
        "timeseries": timeseries,
        "missing_timseries": missing_timeseries,
        "can_edit": can_edit
    }
    html = list(render(request, 'add_run_precheck.html', context))[0]

    payload = {
        'html': html.decode('utf-8')}

    return HttpResponse(json.dumps(payload), content_type="application/json")


@csrf_protect
def show_logs(request):
    """
    Retrieve the logs from a run path

    Parameters:
    model_uuid (uuid): required
    run_id (int): required

    Returns: HttpResponse

    Example:
    POST: /component/show_logs/
    """

    model_uuid = request.POST['model_uuid']
    run_id = request.POST['run_id']

    model = Model.by_uuid(model_uuid)
    model.handle_view_access(request.user)

    try:
        run = Run.objects.get(id=run_id)
    except Exception:
        raise Http404
    with open(run.logs_path) as f:
        html = f.read()
    try:
        tb = run.run_task.traceback
        html += tb.replace("\n", "<br>").replace("    ", "&emsp;&emsp;")
    except Exception:
        pass
    return HttpResponse(html, content_type="text/html")


@csrf_protect
def plot_outputs(request):
    """
    Retrieve the plots from a run path

    Parameters:
    model_uuid (uuid): required
    run_id (int): required

    Returns: HttpResponse

    Example:
    POST: /component/plot_outputs/
    """

    model_uuid = request.POST["model_uuid"]
    run_id = request.POST["run_id"]
    carrier = request.POST.get("carrier", None)
    location = request.POST.get("location", None)
    month = request.POST.get("month", None)

    model = Model.by_uuid(model_uuid)
    model.handle_view_access(request.user)

    try:
        run = Run.objects.get(id=run_id)
    except Exception:
        raise Http404

    data = run.get_viz_data(carrier, location, month)
    return JsonResponse(data)


@csrf_protect
def map_outputs(request):
    """
    Retrieve the data for rendering the nodal network map

    Parameters:
    model_uuid (uuid): required
    run_id (int): required

    Returns: JsonResponse

    Example:
    POST: /component/map_outputs/
    """

    model_uuid = request.POST['model_uuid']
    run_id = request.POST['run_id']
    start_date = pd.to_datetime(request.POST['start_date'])
    end_date = pd.to_datetime(request.POST['end_date']) + pd.DateOffset(days=1)

    model = Model.by_uuid(model_uuid)
    model.handle_view_access(request.user)

    run = model.runs.filter(id=run_id).first()

    response = defaultdict(lambda: None)

    if run is None:
        response["message"] = "To request data, " \
                              "post a valid 'model_uuid' and 'run_id'"
    else:
        # Static
        files = ["inputs_colors",
                 "inputs_names",
                 "inputs_inheritance",
                 "inputs_loc_latitude",
                 "inputs_loc_longitude",
                 "results_energy_cap"]
        for file in files:
            with open(os.path.join(run.outputs_path, file + ".csv")) as f:
                response[file] = f.read()

        # Variable
        files = ["results_flow_in",
                 "results_flow_out"]
        month = None
        if run.get_months():
            month = start_date.month
            month = '0' + str(month) if month < 10 else str(month)
        ext = '_' + str(month) + '.csv' if month else '.csv'
        for file in files:
            df = pd.read_csv(os.path.join(run.outputs_path, file + ext),
                             header=0)
            df.set_index('timesteps', inplace=True, drop=False)
            df.index = pd.to_datetime(df.index)
            df = df[(df.index >= start_date) & (df.index < end_date)]
            s = io.StringIO()
            df.to_csv(s, index=False)
            response[file] = s.getvalue()

    return JsonResponse(response)
