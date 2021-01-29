import base64
import os
import json
from datetime import datetime, timedelta

from django.views.decorators.csrf import csrf_protect, csrf_exempt
from django.conf import settings
from django.http import HttpResponse, HttpResponseRedirect, Http404
from django.core.exceptions import ObjectDoesNotExist
from django.contrib.auth import authenticate

from api.exceptions import ModelNotExistException
from api.models.outputs import Run
from api.models.outputs import Haven, Cambium
from api.tasks import run_model, task_status, build_model
from api.models.configuration import Model, ParamsManager, Model_User
from api.utils import zip_folder
from taskmeta.models import CeleryTask


@csrf_protect
def build(request):
    """
    Build and save the input files (YAML and CSV) for a Calliope run.

    Parameters:
    model_uuid (uuid): required
    scenario_id (int): required
    start_date (timestamp): required
    end_date (timestamp): required

    Returns (json): Action Confirmation

    Example:
    GET: /api/build/
    """

    # Input parameters
    model_uuid = request.GET.get("model_uuid", None)
    scenario_id = request.GET.get("scenario_id", None)
    start_date = request.GET.get("start_date", None)
    end_date = request.GET.get("end_date", None)

    model = Model.by_uuid(model_uuid)
    model.handle_edit_access(request.user)

    try:
        start_date = datetime.strptime(start_date, "%Y-%m-%d")
        end_date = datetime.strptime(end_date,
                                     "%Y-%m-%d") + timedelta(hours=23)
        subset_time = str(start_date.date()) + " to " + str(end_date.date())
        year = start_date.year

        # model and scenario instances
        scenario = model.scenarios.get(id=scenario_id)

        # Create run instance
        run = Run.objects.create(
            model=model,
            scenario=scenario,
            year=year,
            subset_time=subset_time,
            status=task_status.QUEUED,
            inputs_path="",
        )

        # Generate File Path
        timestamp = datetime.now().strftime("%Y-%m-%d %H%M%S")
        model_name = ParamsManager.simplify_name(model.name)
        scenario_name = ParamsManager.simplify_name(scenario.name)
        inputs_path = "{}/{}/{}/{}/{}/{}/{}/inputs".format(
            settings.DATA_STORAGE,
            model.uuid,
            model_name,
            scenario_name,
            year,
            subset_time,
            timestamp,
        )
        inputs_path = inputs_path.lower().replace(" ", "-")
        os.makedirs(inputs_path, exist_ok=True)

        # Celery task
        async_result = build_model.apply_async(
            kwargs={
                "inputs_path": inputs_path,
                "run_id": run.id,
                "model_uuid": model_uuid,
                "scenario_id": scenario_id,
                "start_date": start_date,
                "end_date": end_date,
            }
        )
        build_task, _ = CeleryTask.objects.get_or_create(
            task_id=async_result.id)
        run.build_task = build_task
        run.save()

        payload = {
            "status": "Success",
            "model_uuid": model_uuid,
            "scenario_id": scenario_id,
            "year": start_date.year,
        }

    except Exception as e:
        payload = {
            "status": "Failed",
            "message": "Please contact admin at robert.spencer@nrel.gov ' \
            'regarding this error: {}".format(
                str(e)
            ),
        }

    return HttpResponse(json.dumps(payload, indent=4),
                        content_type="application/json")


@csrf_protect
def optimize(request):
    """
    Optimize a Calliope problem

    Parameters:
    model_uuid (uuid): required
    run_id (int): required

    Returns (json): Action Confirmation

    Example:
    POST: /api/optimize/
    """

    run_id = request.POST["run_id"]
    model_uuid = request.POST["model_uuid"]
    model = Model.by_uuid(model_uuid)
    model.handle_edit_access(request.user)

    payload = {"run_id": run_id}

    # run instance does not exist.
    try:
        run = model.runs.get(id=run_id)
    except ObjectDoesNotExist as e:
        print(e)
        payload["message"] = "Run ID {} does not exist.".format(run_id)
        return HttpResponse(
            json.dumps(payload, indent=4), content_type="application/json"
        )

    # model path does not exist
    model_path = os.path.join(run.inputs_path, "model.yaml")
    if not os.path.exists(model_path):
        payload["message"] = "Invalid model config path!"
        return HttpResponse(
            json.dumps(payload, indent=4), content_type="application/json"
        )

    # run celery task
    async_result = run_model.apply_async(
        kwargs={"run_id": run_id, "model_path": model_path,
                "user_id": request.user.id}
    )
    run_task, _ = CeleryTask.objects.get_or_create(task_id=async_result.id)
    run.run_task = run_task
    run.status = task_status.QUEUED
    run.save()
    payload = {"task_id": async_result.id}
    return HttpResponse(json.dumps(payload, indent=4),
                        content_type="application/json")


@csrf_protect
def delete_run(request):
    """
    Delete a scenario run

    Parameters:
    model_uuid (uuid): required
    run_id (int): required

    Returns (json): Action Confirmation

    Example:
    POST: /api/delete_run/
    """

    model_uuid = request.POST["model_uuid"]
    run_id = request.POST["run_id"]

    model = Model.by_uuid(model_uuid)
    model.handle_edit_access(request.user)

    run = model.runs.filter(id=run_id)
    run.delete()

    # Disabling the file removal b/c duplicated models currently share files

    # if os.path.exists(run.inputs_path):
    #     shutil.rmtree(run.inputs_path)

    # if os.path.exists(run.logs_path):
    #     shutil.rmtree(os.path.dirname(run.logs_path))

    # if os.path.exists(run.plots_path):
    #     shutil.rmtree(os.path.dirname(run.plots_path))

    # if os.path.exists(run.outputs_path):
    #     shutil.rmtree(run.outputs_path)

    return HttpResponseRedirect("")


@csrf_protect
def publish_run(request):
    """
    Publish a scenario run to Cambium (https://cambium.nrel.gov/)

    Parameters:
    model_uuid (uuid): required
    run_id (int): required

    Returns (json): Action Confirmation

    Example:
    POST: /api/publish_run/
    """

    model_uuid = request.POST["model_uuid"]
    run_id = request.POST["run_id"]

    model = Model.by_uuid(model_uuid)
    model.handle_edit_access(request.user)

    run = model.runs.filter(id=run_id).first()
    msg = Cambium.push_run(run)
    payload = {'message': msg}

    return HttpResponse(json.dumps(payload), content_type="application/json")


@csrf_protect
def update_run_description(request):
    """
    Update the description for a run

    Parameters:
    model_uuid (uuid): required
    run_id (int): required
    description (str): required

    Returns (json): Action Confirmation

    Example:
    POST: /api/update_run_description/
    """

    model_uuid = request.POST["model_uuid"]
    run_id = int(request.POST["id"])
    description = request.POST["value"]

    model = Model.by_uuid(model_uuid)
    model.handle_edit_access(request.user)

    try:
        run = model.runs.get(id=run_id)
    except ObjectDoesNotExist as e:
        print(e)
        payload = {}
        payload["message"] = "Run ID {} does not exist.".format(run_id)
        return HttpResponse(
            json.dumps(payload, indent=4), content_type="application/json"
        )

    if description != run.description:
        run.description = description
        run.save()

    payload = description
    return HttpResponse(payload, content_type="text/plain")


def basic_auth_required(api_view):
    def wrapper(request, *args, **kwargs):
        try:
            auth = request.META["HTTP_AUTHORIZATION"].split()
            assert auth[0].lower() == "basic"
            email, password = base64.b64decode(auth[1]).decode("utf-8").split(":")
            user = authenticate(username=email, password=password)
            if user is not None and user.is_active:
                request.user = user
                return api_view(request, *args, **kwargs)
            else:
                msg = "Invalid email or password! Please try again."
                return HttpResponse(json.dumps({"error": msg}),
                                    content_type="application/json")
        except Exception as e:
            msg = str(e)
            if str(e) == "'HTTP_AUTHORIZATION'":
                msg = "Authentorization failed! Please try Basic Auth."
            return HttpResponse(json.dumps({"error": msg}),
                                content_type="application/json")
    return wrapper


@csrf_exempt
@basic_auth_required
def haven(request):
    """
    Retrieve the data for a run

    Parameters:
    model_uuid (uuid): optional
    scenario_id (int): optional
    stations_only (bool): optional
    aggregate (dict): optional, for example, {"solar": [1,2,4]}

    Returns (json): Requested Data

    Example:
    POST: /api/haven/
    """
    if request.method != "POST":
        msg = "Method is not allowed."
        response = HttpResponse(json.dumps({"error": msg}),
                                content_type="application/json")
        return response

    user = request.user
    if not user.is_authenticated:
        msg = "User is not authenticated."
        return HttpResponse(json.dumps({"error": msg}),
                            content_type="application/json")

    # Parse post parameters
    model_uuid = request.POST.get('model_uuid', None)
    scenario_id = request.POST.get('scenario_id', None)
    stations_only = bool(request.POST.get('stations_only', True))
    aggregate = request.POST.get('aggregate', None)

    # Construct initial payload
    payload = {}
    payload["inputs"] = {
        "model_uuid": model_uuid,
        "scenario_id": scenario_id,
        "stations_only": stations_only,
        "aggregage": aggregate
    }

    # Ensure model existing and access
    try:
        model = Model.by_uuid(model_uuid)
        model.handle_view_access(user)
    except ModelNotExistException:
        payload["message"] = f"To request data, post a valid 'model_uuid'."
        model_users = Model_User.objects.filter(user=user,
                                                model__snapshot_version=None)
        models = [{
            "uuid": model_user.model.get_uuid(),
            "name": model_user.model.name
        } for model_user in model_users]
        payload["models"] = models
        return HttpResponse(json.dumps(payload),
                            content_type="application/json")

    # Query user requested data.
    payload["selected_model_name"] = model.name
    scenario = model.scenarios.filter(id=scenario_id).first()
    if scenario is None:
        payload["message"] = "To request data, post a valid 'scenario_id'."
        scenarios = list(model.scenarios.values('id', 'name'))
        payload["scenarios"] = scenarios
    else:
        payload["selected_scenario_name"] = scenario.name
        try:
            haven_data = Haven(scenario).get_data(aggregate, stations_only)
            if isinstance(haven_data, str):
                payload["message"] = haven_data
            else:
                payload["message"] = "All data successfully retrieved."
                payload["scenario_data"] = haven_data
        except Exception as e:
            payload["message"] = str(e)

    return HttpResponse(json.dumps(payload), content_type="application/json")


@csrf_protect
def download(request):
    """
    Download files from a path to client machine

    Parameters:
    model_uuid (uuid): required
    run_id (int): required

    Returns (json): Action Confirmation

    Example:
    GET: /api/download/
    """
    model_uuid = request.GET['model_uuid']
    run_id = request.GET['run_id']
    download_type = request.GET['type']

    model = Model.by_uuid(model_uuid)
    model.handle_view_access(request.user)
    
    try:
        run = Run.objects.get(id=run_id)
    except Exception:
        raise Http404
    
    if download_type == 'inputs':
        path = run.inputs_path
    elif download_type == "outputs":
        path = run.outputs_path
    else:
        raise Http404
    
    if os.path.exists(path):
        file_path = zip_folder(path)
        with open(file_path, 'rb') as fh:
            response = HttpResponse(fh.read(), content_type="application/text")
            response['Content-Disposition'] = 'inline; filename=' + os.path.basename(file_path)
            return response

    return HttpResponse(
        json.dumps({"message": "Not Found!"}, indent=4),
        content_type="application/json"
    )
