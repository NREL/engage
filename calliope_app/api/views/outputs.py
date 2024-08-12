import base64
import json
import io
import logging
import os
import shutil
import zipfile
import sys
from re import match

from datetime import datetime, timedelta
from urllib.parse import urljoin
import requests
import pandas as pd
import pint

from celery import current_app,chain
from django.views.decorators.csrf import csrf_protect
from django.conf import settings
from django.http import HttpResponse, HttpResponseRedirect, Http404
from django.core.exceptions import ObjectDoesNotExist
from django.contrib.auth import authenticate
from django.core.files.storage import FileSystemStorage
from django.shortcuts import redirect, render
from django.contrib.auth.decorators import login_required
from django.utils.text import slugify

from api.models.outputs import Run, Cambium
from api.tasks import run_model, task_status, build_model,upload_ts
from api.models.calliope import Abstract_Tech, Abstract_Tech_Param, Parameter, Run_Parameter
from api.models.configuration import (
    Model, ParamsManager, User_File, Location, Technology,
    Tech_Param, Loc_Tech, Loc_Tech_Param, Timeseries_Meta, Carrier, Scenario_Param
)

from api.models.engage import ComputeEnvironment
from api.utils import zip_folder, initialize_units, convert_units, noconv_units
from batch.managers import AWSBatchJobManager
from taskmeta.models import CeleryTask, BatchTask, batch_task_status

from calliope_app.celery import app

logger = logging.getLogger(__name__)


@csrf_protect
def build(request):
    """
    Build and save the input files (YAML and CSV) for a Calliope run.

    Parameters:
    model_uuid (uuid): required
    scenario_id (int): required
    start_date (timestamp): required
    end_date (timestamp): required
    cluster (bool): optional
    manual (bool): optional

    Returns (json): Action Confirmation

    Example:
    GET: /api/build/
    """
    parameters = request.GET.get('parameters', None)
    parameters = json.loads(parameters)

    # Input parameters
    model_uuid = request.GET.get("model_uuid", None)
    scenario_id = request.GET.get("scenario_id", None)
    start_date = request.GET.get("start_date", None)
    end_date = request.GET.get("end_date", None)
    cluster = (request.GET.get("cluster", 'true') == 'true')
    manual = (request.GET.get("manual", 'false') == 'true')
    run_env = request.GET.get("run_env", None)
    timestep = request.GET.get("timestep", '1H')
    notes = request.GET.get("notes","")
    years = [int(y) for y in request.GET.get("years",'').split(',') if y.strip() != '']
    try:
        pd.tseries.frequencies.to_offset(timestep)
    except ValueError:
        payload = {
            "status": "Failed",
            "message": "'"+timestep+"' is not a valid timestep.",
        }

    model = Model.by_uuid(model_uuid)
    model.handle_edit_access(request.user)


    try:
        start_date = datetime.strptime(start_date, "%Y-%m-%d")
        end_date = datetime.strptime(end_date,
                                     "%Y-%m-%d") + timedelta(hours=23)

        # model and scenario instances
        scenario = model.scenarios.get(id=scenario_id)

        # compute environment of the run
        try:
            compute_environment = ComputeEnvironment.objects.get(name=run_env)
        except ComputeEnvironment.DoesNotExist:
            compute_environment = ComputeEnvironment.objects.filter(is_default=True).first(0)

        timestamp = datetime.now().strftime("%Y-%m-%d %H%M%S").lower().replace(" ", "-")
        if not years:
            years = [start_date.year]
            groupname = ''
        else:
            if start_date.year not in years:
                years = [start_date.year]+years
            groupname = 'Group-'+timestamp
        for year in sorted(years):

            start_date = start_date.replace(year=year)
            end_date = end_date.replace(year=year)
            subset_time = str(start_date.date()) + " to " + str(end_date.date())
            # Create run instance
            run = Run.objects.create(
                model=model,
                scenario=scenario,
                year=year,
                subset_time=subset_time,
                status=task_status.QUEUED,
                inputs_path="",
                cluster=cluster,
                manual=manual,
                timestep=timestep,
                compute_environment=compute_environment,
                group=groupname,
                description=notes
            )

            # Generate File Path
            model_name = ParamsManager.simplify_name(model.name)
            scenario_name = ParamsManager.simplify_name(scenario.name)
            if groupname:
                inputs_path = "{}/{}/{}/{}/{}/{}/{}/{}/inputs".format(
                    settings.DATA_STORAGE,
                    model.uuid,
                    model_name,
                    scenario_name,
                    groupname,
                    year,
                    subset_time,
                    timestamp,
                )
            else:
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
            
            run.run_options = []
            for id in parameters.keys():
                run_parameter= Run_Parameter.objects.get(pk=int(id))
                run.run_options.append({'root':run_parameter.root,'name':run_parameter.name,'value':parameters[id]})
           
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

            build_task = CeleryTask.objects.get(task_id=async_result.id)
            run.build_task = build_task
            run.save()

            logger.info("Model run %s starts to build in celery worker.", run.id)

        payload = {
            "status": "Success",
            "model_uuid": model_uuid,
            "scenario_id": scenario_id,
            "year": start_date.year,
        }

    except Exception as e:
        logger.warning("Failed to build model run.")
        logger.exception(e)
        payload = {
            "status": "Failed",
            "message": "Please contact admin at engage@nrel.gov ' \
            'regarding this error: {}".format(
                str(e)
            ),
        }
    return HttpResponse(json.dumps(payload, indent=4), content_type="application/json")


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
        logger.warning(e)

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
    environment = run.compute_environment
    if environment.type == "Celery Worker":
        if run.group != '':
            chain_runs = [(run.id,model_path,request.user.id)]
            future_runs = Run.objects.filter(model=model,group=run.group,year__gt=run.year).order_by('year')
            for next_run in future_runs:
                if next_run.status == task_status.BUILT:
                    logger.info("Found a subsequent gradient model for year %s.",next_run.year)
                    next_model_path = os.path.join(next_run.inputs_path, "model.yaml")
                    if not os.path.exists(model_path):
                        logger.warning("Invalid model config path! Gradient year skipped.")
                    chain_runs.append((next_run.id,next_model_path,request.user.id))
            group_chain = chain(run_model.si(run_id=c[0],model_path=c[1],user_id=c[2]) for c in chain_runs).apply_async()
            run_task, _ = CeleryTask.objects.get_or_create(task_id=group_chain.id)
            Run.objects.filter(model=model,group=run.group).update(run_task=run_task,status=task_status.QUEUED)
            payload = {"task_id":group_chain.id}
        else:
            async_result = run_model.apply_async(
                kwargs={
                    "run_id": run_id,
                    "model_path": model_path,
                    "user_id": request.user.id
                }
            )
            logger.info(
                "Model run %s starts to execute in %s compute environment with celery worker.",
                run.id, environment.name
            )

            run_task, _ = CeleryTask.objects.get_or_create(task_id=async_result.id)
            run.run_task = run_task
            run.status = task_status.QUEUED
            run.save()
            payload = {"task_id": async_result.id}

    # Batch task
    elif environment.type == "Container Job":
        manager = AWSBatchJobManager(compute_environment=environment)

        # Try to fetch and update Batch job status
        _runs = Run.objects.filter(
            compute_environment__name=environment.name,
            status__in=[task_status.QUEUED, task_status.RUNNING]
        )
        result, all_complete = manager.describe_jobs(jobs=list({r.batch_job.task_id for r in _runs}))
        logger.info("Current uncomplete Batch job status: %s", result)
        for r in _runs:
            if r.batch_job.task_id not in result:
                continue
            job_status = result[r.batch_job.task_id]
            if job_status == "SUCCEEDED":
                r.status = task_status.SUCCESS
                r.batch_job.status = batch_task_status.SUCCEEDED
            if job_status == "FAILED":
                r.status = task_status.FAILURE
                r.batch_job.status = batch_task_status.FAILED
            r.batch_job.save()
            r.save()
        
        if not all_complete:
            payload = {
                "status": "BLOCKED",
                "message": f"Compute environment '{environment.name}' is in use, please try again later."
            }
        else:
            job = manager.generate_job_message(run_id=run.id, user_id=request.user.id, depends_on=[])
            response = manager.submit_job(job)
            logger.info(
                "Model run %s starts to execute in '%s' comptute environment with container job.",
                run.id, environment.name
            )
            try:
                batch_job = BatchTask.objects.get(task_id=response["jobId"])
            except BatchTask.DoesNotExist:
                batch_job = BatchTask.objects.create(task_id=response["jobId"], status=batch_task_status.SUBMITTED)
            run.batch_job = batch_job
            run.status = task_status.QUEUED
            run.save()
            payload = {"task_id": response.get("jobId")}
            if run.group != '':
                future_runs = Run.objects.filter(group=run.group,year__gt=run.year).order_by('year')
                for next_run in future_runs:
                    if next_run.status == task_status.BUILT:
                        logger.info("Found a subsequent gradient model for year %s.",next_run.year)
                        job = manager.generate_job_message(run_id=next_run.id, user_id=request.user.id,
                                                            depends_on=[run.batch_job.task_id])
                        response = manager.submit_job(job)
                        logger.info(
                            "Graidient model run %s queued to execute in '%s' comptute environment with container job waiting on run %s.",
                            next_run.id, environment.name, run.id
                        )
                        try:
                            batch_job = BatchTask.objects.get(task_id=response["jobId"])
                        except BatchTask.DoesNotExist:
                            batch_job = BatchTask.objects.create(task_id=response["jobId"], status=batch_task_status.SUBMITTED)
                        next_run.batch_job = batch_job
                        next_run.status = task_status.QUEUED
                        next_run.save()
                        run = next_run
                    else:
                        logger.info("Found a subsequent gradient model for year %s but it was not built.",next_run.year)
                        break
    
    # Unknown environment, not supported
    else:
        raise Exception("Failed to submit job, unknown compute environment")

    return HttpResponse(json.dumps(payload, indent=4),  content_type="application/json")


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

    run = model.runs.get(id=run_id)
    if run.outputs_key:
        data = {
            'filename': run.outputs_key,
            'project_uuid': str(model.uuid),
            'private_key': settings.CAMBIUM_API_KEY,
        }
        try:
            url = urljoin(settings.CAMBIUM_URL, "api/remove-data/")
            requests.post(url, data=data).json()
        except Exception as e:
            logger.warning("Cambium removal failed")
            logger.exception(e)

    # Terminate Celery Task
    if run.run_task and run.run_task.status not in [task_status.FAILURE, task_status.SUCCESS]:
        task_id = run.run_task.task_id
        current_app.control.revoke(task_id, terminate=True)
        run.run_task.status = task_status.FAILURE
        run.run_task.result = ""
        run.run_task.traceback = f"Task terminated manually by Engage user: {request.user.email}"
        run.run_task.save()

    # Terminate Container Job
    if run.batch_job:
        job_id = run.batch_job.task_id
        reason = f"Job terminated manually by Engage user: {request.user.email}"
        manager = AWSBatchJobManager(compute_environment=run.compute_environment)
        try:
            manager.terminate_job(job_id, reason)
            logger.info("Batch job terminated by user %s", request.user.email)
        except:
            pass

        run.batch_job.status = batch_task_status.FAILED
        run.batch_job.result = ""
        run.batch_job.traceback = reason
        run.batch_job.save()

    run.delete()

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
        logger.exception(e)
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
            response['Content-Disposition'] = 'inline; filename='+slugify(model.name+'_'+run.scenario.name+'_'+str(run.year)+'_')+os.path.basename(file_path)
            return response

    return HttpResponse(
        json.dumps({"message": "Not Found!"}, indent=4),
        content_type="application/json"
    )

@csrf_protect
def upload_outputs(request):
    """
    Upload a zipped outputs file.

    Parameters:
    model_uuid (uuid): required
    run_id (int): required
    description (str): optional
    myfile (file): required

    Returns:

    Example:
    POST: /api/upload_outputs/
    """

    model_uuid = request.POST["model_uuid"]
    run_id = request.POST["run_id"]

    model = Model.by_uuid(model_uuid)
    model.handle_edit_access(request.user)

    try:
        run = Run.objects.get(id=run_id)
    except Exception:
        logger.warning("No Run Found")
        raise Http404

    if (request.method == "POST") and ("myfile" in request.FILES):

        myfile = request.FILES["myfile"]
        if os.path.splitext(myfile.name)[1].lower() == '.zip':

            model_dir = run.inputs_path.replace("/inputs","")
            out_dir = os.path.join(model_dir,"outputs")
            if not os.path.exists(out_dir):
                os.makedirs(out_dir, exist_ok=True)

            fs = FileSystemStorage()
            filename = os.path.basename(fs.save(os.path.join(out_dir,myfile.name), myfile))

            # Default assumes CSV files were directly zipped into archive
            run.outputs_path = out_dir
            with zipfile.ZipFile(os.path.join(out_dir,filename),'r') as zip_f:
                zip_f.extractall(out_dir)
            #shutil.unpack_archive(filename,out_dir)
            # Loop through options for archived output directories rather than base CSVs
            # TODO: Add user input on location of output CSVs via API option
            for dir in ['outputs','model_outputs']:
                if dir in os.listdir(out_dir):
                    run.outputs_path = os.path.join(out_dir,dir)

            run.save()

            return redirect("/%s/runs/" % model_uuid)
        return redirect("/%s/runs/" % model_uuid)

    logger.warning("No File Found")
    raise Http404

@csrf_protect
@login_required
def upload_locations(request):
    """
    Upload a CSV file with new/updated locations.

    Parameters:
    model_uuid (uuid): required
    description (str): optional
    myfile (file): required
    col_map (dict): optional

    Returns:

    Example:
    POST: /api/upload_locations/
    """

    model_uuid = request.POST["model_uuid"]

    model = Model.by_uuid(model_uuid)
    model.handle_edit_access(request.user)

    context = {
                'logs':[],
                "model": model
              }

    if (request.method == "POST") and ("myfile" in request.FILES):

        myfile = request.FILES["myfile"]
        if os.path.splitext(myfile.name)[1].lower() == '.csv':
            df = pd.read_csv(myfile)
        else:
            context['logs'].append('File format not supported. Please use a .csv.')
            return render(request, "bulkresults.html", context)

        if not set(['pretty_name','longitude','latitude']).issubset(set(df.columns)):
            context['logs'].append('Missing required columns. pretty_name, longitude, latitude are required.')
            return render(request, "bulkresults.html", context)
        df = df.loc[:,df.columns.isin(['id','pretty_name','longitude','latitude','available_area','description'])]
        df['model_id'] = model.id
        df['name'] = df['pretty_name'].apply(lambda x: ParamsManager.simplify_name(x))
        for i,row in df.iterrows():
            if pd.isnull(row['pretty_name']):
                context['logs'].append(str(i)+'- Missing pretty name. Skipped')
                continue
            if pd.isnull(row['latitude']) or pd.isnull(row['longitude']):
                context['logs'].append(str(i)+'- Missing latitude or longitude. Skipped')
                continue
            if 'available_are' not in row or pd.isnull(row['available_area']):
                row['available_area'] = None
            if 'description' not in row or pd.isnull(row['description']):
                row['description'] = None
            if 'id' not in row.keys() or pd.isnull(row['id']):
                location = Location.objects.create(**(row.dropna()))
            else:
                location = Location.objects.filter(id=row['id']).first()
                if not location:
                    context['logs'].append(str(i)+'- Location '+row['pretty_name']+': No location with id '+str(row['id'])+' found to update. Skipped.')
                    continue
                location.name = row['name']
                location.pretty_name = row['pretty_name']
                location.longitude = row['longitude']
                location.latitude = row['latitude']
                location.available_area = row['available_area']
                location.description = row['description']
                location.save()

        return render(request, "bulkresults.html", context)

    context['logs'].append("No file found")
    return render(request, "bulkresults.html", context)


@csrf_protect
@login_required
def upload_techs(request):
    """
    Upload a CSV file with new/updated technologies.

    Parameters:
    model_uuid (uuid): required
    description (str): optional
    myfile (file): required
    col_map (dict): optional

    Returns:

    Example:
    POST: /api/upload_techs/
    """

    model_uuid = request.POST["model_uuid"]

    model = Model.by_uuid(model_uuid)
    model.handle_edit_access(request.user)

    context = {
                'logs':[],
                "model": model
              }

    if (request.method == "POST") and ("myfile" in request.FILES):

        myfile = request.FILES["myfile"]
        if os.path.splitext(myfile.name)[1].lower() == '.csv':
            df = pd.read_csv(myfile)
        else:
            context['logs'].append('File format not supported. Please use a .csv.')
            return render(request, "bulkresults.html", context)

        if not set(['pretty_name','abstract_tech']).issubset(set(df.columns)):
            context['logs'].append('Missing required columns. pretty_name, abstract_tech are required.')
            return render(request, "bulkresults.html", context)

        df['name'] = df['pretty_name'].apply(lambda x: ParamsManager.simplify_name(str(x)))
        if 'pretty_tag' in df.columns:
            df['tag'] = df['pretty_tag'].apply(lambda x: ParamsManager.simplify_name(str(x)))

        ureg = initialize_units()

        for i,row in df.iterrows():
            try:
                if pd.isnull(row['abstract_tech']):
                    context['logs'].append(str(i)+'- Tech '+row['pretty_name']+': Missing abstract_tech. Skipped.')
                    continue
                if row['abstract_tech'] in ['conversion','conversion_plus']:
                    if 'carrier_in' not in row.keys() or 'carrier_out' not in row.keys() or pd.isnull(row['carrier_in']) or pd.isnull(row['carrier_out']):
                        context['logs'].append(str(i)+'- Tech '+str(row['pretty_name'])+': Conversion techs require both carrier_in and carrier_out. Skipped.')
                        continue
                else:
                    if 'carrier' not in row.keys() or pd.isnull(row['carrier']):
                        context['logs'].append(str(i)+'- Tech '+str(row['pretty_name'])+': Missing a carrier. Skipped.')
                        continue

                if 'id' not in row.keys() or pd.isnull(row['id']):
                    if pd.isnull(row['tag']):
                        technology = Technology.objects.create(
                            model_id=model.id,
                            abstract_tech_id=Abstract_Tech.objects.filter(name=row['abstract_tech']).first().id,
                            name=row['name'],
                            pretty_name=row['pretty_name'],
                        )
                    else:
                        technology = Technology.objects.create(
                            model_id=model.id,
                            abstract_tech_id=Abstract_Tech.objects.filter(name=row['abstract_tech']).first().id,
                            name=row['name'],
                            pretty_name=row['pretty_name'],
                            tag=row['tag'],
                            pretty_tag=row['pretty_tag']
                        )

                else:
                    technology = Technology.objects.filter(model=model,id=row['id']).first()
                    if not technology:
                        context['logs'].append(str(i)+'- Tech '+str(row['pretty_name'])+': No tech with id '+str(row['id'])+' found to update. Skipped.')
                        continue
                    technology.abstract_tech = Abstract_Tech.objects.filter(name=row['abstract_tech']).first()
                    technology.name = row['name']
                    technology.pretty_name = row['pretty_name']
                    if pd.isnull(row['tag']) or pd.isnull(row['pretty_tag']):
                        technology.tag = None
                        technology.pretty_tag = None
                    else:
                        technology.tag = row['tag']
                        technology.pretty_tag = row['pretty_tag']
                    technology.save()
                    Tech_Param.objects.filter(model_id=model.id,technology_id=technology.id).delete()

                Tech_Param.objects.create(
                        model_id=model.id,
                        technology_id=technology.id,
                        parameter_id=Parameter.objects.filter(name='base_tech').first().id,
                        value=row['abstract_tech'],
                    )
                Tech_Param.objects.create(
                        model_id=model.id,
                        technology_id=technology.id,
                        parameter_id=Parameter.objects.filter(name='name').first().id,
                        value=row['pretty_name'],
                    )
                update_dict = {'edit':{'parameter':{},'timeseries':{}},'add':{},'essentials':{}}
                # Grab in/out carriers and their units
                units_in_ids= ParamsManager.get_tagged_params('units_in')
                units_out_ids= ParamsManager.get_tagged_params('units_out')
                units_in_names = Parameter.objects.filter(id__in=units_in_ids).values_list('name', flat=True)
                carrier_in_name = [row[c] for c in units_in_names if c in row][0]
                units_out_names = Parameter.objects.filter(id__in=units_out_ids).values_list('name', flat=True)
                carrier_out_name = [row[c] for c in units_out_names if (c in row and not pd.isnull(row[c]))][0]

                carrier_in = Carrier.objects.filter(model=model,name=carrier_in_name)
                if carrier_in:
                    carrier_in = carrier_in.first()
                    in_rate = carrier_in.rate_unit
                    in_quantity = carrier_in.quantity_unit
                else:
                    in_rate = 'kW'
                    in_quantity = 'kWh'
                carrier_out = Carrier.objects.filter(model=model,name=carrier_out_name)
                if carrier_out:
                    carrier_out = carrier_out.first()
                    out_rate = carrier_out.rate_unit
                    out_quantity = carrier_out.quantity_unit
                else:
                    out_rate = 'kW'
                    out_quantity = 'kWh'
                for f,v in row.iteritems():
                    if pd.isnull(v):
                        continue
                    pyear = f.rsplit('_',1)
                    if len(pyear) > 1 and match('[0-9]{4}',pyear[1]):
                        proot = pyear[0].rsplit('.',1)
                        if len(proot) > 1:
                            p = Parameter.objects.filter(root=proot[0],name=proot[1]).first()
                        else:
                            p = Parameter.objects.filter(name=pyear[0]).first()
                        if p is None:
                            p = Parameter.objects.filter(name=f).first()
                            if p is None:
                                continue
                        else:
                            pyear = pyear[1]
                    else:
                        pyear = None
                        proot = f.rsplit('.',1)
                        if len(proot) > 1:
                            p = Parameter.objects.filter(root=proot[0],name=proot[1]).first()
                        else:
                            p = Parameter.objects.filter(name=f).first()
                        if p is None:
                            continue
                    # Essential params
                    if p.is_essential:
                        update_dict['essentials'][p.pk] = v

                    # Timeseries params
                    elif str(v).startswith('file='):
                        fields = v.split('=')[1].split(':')
                        filename = fields[0]
                        t_col = fields[1]
                        v_col = fields[2]

                        file = User_File.objects.filter(model=model, filename='user_files/'+filename)
                        if not file:
                            context['logs'].append(str(i)+'- Tech '+str(row['pretty_name'])+': Column '+f+' missing file "' + filename+ '" for timeseries. Parameter skipped.')
                            continue

                        existing = Timeseries_Meta.objects.filter(model=model,
                                                original_filename=filename,
                                                original_timestamp_col=t_col,
                                                original_value_col=v_col).first()
                        if not existing:
                            existing = Timeseries_Meta.objects.create(
                                model=model,
                                name=filename+str(t_col)+str(v_col),
                                original_filename=filename,
                                original_timestamp_col=t_col,
                                original_value_col=v_col,
                            )
                            try:
                                async_result = upload_ts.apply_async(
                                    kwargs={
                                        "model_uuid": model_uuid,
                                        "timeseries_meta_id": existing.id,
                                        "file_id": file.first().id,
                                        "timestamp_col": t_col,
                                        "value_col": v_col,
                                        "has_header": True,
                                    }
                                )
                                upload_task = CeleryTask.objects.get(task_id=async_result.id)
                                existing.upload_task = upload_task
                                existing.is_uploading = True
                                existing.save()
                            except Exception as e:
                                context['logs'].append(str(e))
                        update_dict['edit']['timeseries'][p.pk] = existing.id
                    else:
                        if p.units in noconv_units:
                            if pyear:
                                if p.pk not in update_dict['add']:
                                    update_dict['add'][p.pk] = {'year':[],'value':[]}
                                if p.pk in update_dict['edit']['parameter']:
                                    update_dict['add'][p.pk]['year'].append('0')
                                    update_dict['add'][p.pk]['value'].append(update_dict['edit']['parameter'][p.pk])
                                    update_dict['edit']['parameter'].pop(p.pk)
                                update_dict['add'][p.pk]['year'].append(pyear)
                                update_dict['add'][p.pk]['value'].append(v)
                            elif p.pk in update_dict['add']:
                                update_dict['add'][p.pk]['year'].append('0')
                                update_dict['add'][p.pk]['value'].append(v)
                            else:
                                update_dict['edit']['parameter'][p.pk] = v
                        else:
                            try:
                                p_units = p.units.replace('[[in_rate]]',in_rate).replace('[[in_quantity]]',in_quantity).replace('[[out_rate]]',out_rate).replace('[[out_quantity]]',out_quantity)
                                if pyear:
                                    if p.pk not in update_dict['add']:
                                        update_dict['add'][p.pk] = {'year':[],'value':[]}
                                    if p.pk in update_dict['edit']['parameter']:
                                        update_dict['add'][p.pk]['year'].append('0')
                                        update_dict['add'][p.pk]['value'].append(update_dict['edit']['parameter'][p.pk])
                                        update_dict['edit']['parameter'].pop(p.pk)
                                    update_dict['add'][p.pk]['year'].append(pyear)
                                    update_dict['add'][p.pk]['value'].append(convert_units(ureg,v,p_units))
                                elif p.pk in update_dict['add']:
                                    update_dict['add'][p.pk]['year'].append('0')
                                    update_dict['add'][p.pk]['value'].append(v)
                                else:
                                    update_dict['edit']['parameter'][p.pk] = convert_units(ureg,v,p_units)
                            except Exception as e:
                                context['logs'].append(str(i)+'- Tech '+str(row['pretty_name'])+': Column '+f+' '+str(e)+'. Error converting units. Parameter skipped.')
                                continue
                technology.update(update_dict)
            except Exception as e:
                logger.warning('ERROR in upload_techs')
                logger.exception(e)
                context['logs'].append('Unexpected error occured at row '+str(i)+': '+str(e))

        return render(request, "bulkresults.html", context)

    context['logs'].append("No file found")
    return render(request, "bulkresults.html", context)

@csrf_protect
@login_required
def upload_loctechs(request):
    """
    Upload a CSV file with new/updated location technologies.

    Parameters:
    model_uuid (uuid): required
    description (str): optional
    myfile (file): required
    col_map (dict): optional

    Returns:

    Example:
    POST: /api/upload_loctechs/
    """

    model_uuid = request.POST["model_uuid"]

    model = Model.by_uuid(model_uuid)
    model.handle_edit_access(request.user)

    context = {
                'logs':[],
                "model": model
              }

    if (request.method == "POST") and ("myfile" in request.FILES):

        myfile = request.FILES["myfile"]
        if os.path.splitext(myfile.name)[1].lower() == '.csv':
            df = pd.read_csv(myfile)
        else:
            context['logs'].append('File format not supported. Please use a .csv.')
            return render(request, 'bulkresults.html', context)

        if not set(['technology','location_1']).issubset(set(df.columns)):
            context['logs'].append("Missing required columns. technology, location_1 are required.")
            return render(request, 'bulkresults.html', context)
        df['tech'] = df['technology'].apply(lambda x: ParamsManager.simplify_name(str(x)))
        if 'pretty_tag' in df.columns:
            df['tag'] = df['pretty_tag'].apply(lambda x: ParamsManager.simplify_name(str(x)))
        elif 'tag' in df.columns:
            df['tag'] = df['tag'].apply(lambda x: ParamsManager.simplify_name(str(x)))
        if 'tag' not in df.columns:
            df['tag'] = None
        df['loc'] = df['location_1'].apply(lambda x: ParamsManager.simplify_name(str(x)))

        ureg = initialize_units()

        for i,row in df.iterrows():
            try:
                if pd.isnull(row['tag']):
                    row['tag'] = None
                technology = Technology.objects.filter(model_id=model.id,pretty_name=row['technology'],tag=row['tag']).first()
                if technology == None:
                    technology = Technology.objects.filter(model_id=model.id,name=row['technology'],tag=row['tag']).first()
                    if technology == None:
                        if pd.isnull(row['tag']):
                            context['logs'].append(str(i)+'- Tech '+str(row['technology'])+' missing. Skipped.')
                        else:
                            context['logs'].append(str(i)+'- Tech '+str(row['technology'])+'-'+str(row['tag'])+' missing. Skipped.')
                        continue

                # Grab in/out carriers and their units
                units_in_ids= ParamsManager.get_tagged_params('units_in')
                units_out_ids= ParamsManager.get_tagged_params('units_out')
                carrier_in_param = Tech_Param.objects.filter(technology=technology, parameter_id__in=units_in_ids).first()
                carrier_out_param = Tech_Param.objects.filter(technology=technology, parameter_id__in=units_out_ids).first()

                carrier_in = Carrier.objects.filter(model=model,name=carrier_in_param.value)
                if carrier_in:
                    carrier_in = carrier_in.first()
                    in_rate = carrier_in.rate_unit
                    in_quantity = carrier_in.quantity_unit
                else:
                    in_rate = 'kW'
                    in_quantity = 'kWh'
                carrier_out = Carrier.objects.filter(model=model,name=carrier_out_param.value)
                if carrier_out:
                    carrier_out = carrier_out.first()
                    out_rate = carrier_out.rate_unit
                    out_quantity = carrier_out.quantity_unit
                else:
                    out_rate = 'kW'
                    out_quantity = 'kWh'

                location = Location.objects.filter(model_id=model.id,pretty_name=row['location_1']).first()
                if location==None:
                    location = Location.objects.filter(model_id=model.id,name=row['location_1']).first()
                    if location==None:
                        context['logs'].append(str(i)+'- Location '+str(row['location_1'])+' missing. Skipped.')
                        continue
                if Abstract_Tech.objects.filter(id=technology.abstract_tech_id).first().name == 'transmission':
                    location_2 = Location.objects.filter(model_id=model.id,pretty_name=row['location_2']).first()
                    if location_2==None:
                        location_2 = Location.objects.filter(model_id=model.id,name=row['location_2']).first()
                        if location_2==None:
                            context['logs'].append(str(i)+'- Location 2 '+str(row['location_2'])+' missing. Skipped.')
                            continue
                    if 'id' not in row.keys() or pd.isnull(row['id']):
                        loctech = Loc_Tech.objects.create(
                            model_id=model.id,
                            technology=technology,
                            location_1=location,
                            location_2=location_2,
                        )
                    else:
                        loctech = Loc_Tech.objects.filter(model=model,id=row['id']).first()
                        if not loctech:
                            context['logs'].append(str(i)+'- Tech '+str(row['technology'])+': No tech with id '+str(row['id'])+' found to update. Skipped.')
                            continue
                        loctech.technology = technology
                        loctech.location_1 = location
                        loctech.location_2 = location_2
                        loctech.save()
                        Loc_Tech_Param.objects.filter(model_id=model.id,loc_tech_id=loctech.id).delete()
                else:
                    if 'id' not in row.keys() or pd.isnull(row['id']):
                        loctech = Loc_Tech.objects.create(
                            model_id=model.id,
                            technology=technology,
                            location_1=location,
                        )
                    else:
                        loctech = Loc_Tech.objects.filter(model=model,id=row['id']).first()
                        if not loctech:
                            context['logs'].append(str(i)+'- Tech '+str(row['technology'])+': No tech with id '+str(row['id'])+' found to update. Skipped.')
                            continue
                        loctech.technology = technology
                        loctech.location_1 = location
                        loctech.save()
                        Loc_Tech_Param.objects.filter(model_id=model.id,loc_tech_id=loctech.id).delete()

                update_dict = {'edit':{'parameter':{},'timeseries':{}},'add':{},'essentials':{}}
                for f,v in row.iteritems():
                    if pd.isnull(v):
                        continue
                    pyear = f.rsplit('_',1)
                    if len(pyear) > 1 and match('[0-9]{4}',pyear[1]):
                        proot = pyear[0].rsplit('.',1)
                        if len(proot) > 1:
                            p = Parameter.objects.filter(root=proot[0],name=proot[1]).first()
                        else:
                            p = Parameter.objects.filter(name=pyear[0]).first()
                        if p is None:
                            p = Parameter.objects.filter(name=f).first()
                            if p is None:
                                continue
                        else:
                            pyear = pyear[1]
                    else:
                        pyear = None
                        proot = f.rsplit('.',1)
                        if len(proot) > 1:
                            p = Parameter.objects.filter(root=proot[0],name=proot[1]).first()
                        else:
                            p = Parameter.objects.filter(name=f).first()
                        if p is None:
                            continue
                    # Essential params
                    if p.is_essential:
                        update_dict['essentials'][p.pk] = v

                    # Timeseries params
                    elif str(v).startswith('file='):
                        fields = v.split('=')[1].split(':')
                        filename = fields[0]
                        t_col = fields[1]
                        v_col = fields[2]

                        file = User_File.objects.filter(model=model, filename='user_files/'+filename)
                        if not file:
                            context['logs'].append(str(i)+'- Tech '+str(row['technology'])+': Column '+f+' missing file "' + filename+ '" for timeseries. Parameter skipped.')
                            continue

                        existing = Timeseries_Meta.objects.filter(model=model,
                                                original_filename=filename,
                                                original_timestamp_col=t_col,
                                                original_value_col=v_col).first()
                        if not existing:
                            existing = Timeseries_Meta.objects.create(
                                model=model,
                                name=filename+str(t_col)+str(v_col),
                                original_filename=filename,
                                original_timestamp_col=t_col,
                                original_value_col=v_col,
                            )
                            try:
                                async_result = upload_ts.apply_async(
                                    kwargs={
                                        "model_uuid": model_uuid,
                                        "timeseries_meta_id": existing.id,
                                        "file_id": file.first().id,
                                        "timestamp_col": t_col,
                                        "value_col": v_col,
                                        "has_header": True,
                                    }
                                )
                                upload_task = CeleryTask.objects.get(task_id=async_result.id)
                                existing.upload_task = upload_task
                                existing.is_uploading = True
                                existing.save()
                            except Exception as e:
                                context['logs'].append(e)
                        update_dict['edit']['timeseries'][p.pk] = existing.id
                    # Timeseries params (based on name)
                    elif str(v).startswith('ts='):
                        tsname = v.split('=')[1]
                        existing = Timeseries_Meta.objects.filter(model=model,
                                                name=tsname).first()
                        if not existing:
                            context['logs'].append(str(i)+'- Tech '+str(row['technology'])+': Column '+f+' missing timeseries "' + tsname + '". Parameter skipped.')
                            continue
                        update_dict['edit']['timeseries'][p.pk] = existing.id
                    else:
                        if p.units in noconv_units:
                            if pyear:
                                if p.pk not in update_dict['add']:
                                    update_dict['add'][p.pk] = {'year':[],'value':[]}
                                if p.pk in update_dict['edit']['parameter']:
                                    update_dict['add'][p.pk]['year'].append('0')
                                    update_dict['add'][p.pk]['value'].append(update_dict['edit']['parameter'][p.pk])
                                    update_dict['edit']['parameter'].pop(p.pk)
                                update_dict['add'][p.pk]['year'].append(pyear)
                                update_dict['add'][p.pk]['value'].append(v)
                            elif p.pk in update_dict['add']:
                                update_dict['add'][p.pk]['year'].append('0')
                                update_dict['add'][p.pk]['value'].append(v)
                            else:
                                update_dict['edit']['parameter'][p.pk] = v
                        else:
                            try:
                                p_units = p.units.replace('[[in_rate]]',in_rate).replace('[[in_quantity]]',in_quantity).replace('[[out_rate]]',out_rate).replace('[[out_quantity]]',out_quantity)
                                if pyear:
                                    if p.pk not in update_dict['add']:
                                        update_dict['add'][p.pk] = {'year':[],'value':[]}
                                    if p.pk in update_dict['edit']['parameter']:
                                        update_dict['add'][p.pk]['year'].append('0')
                                        update_dict['add'][p.pk]['value'].append(update_dict['edit']['parameter'][p.pk])
                                        update_dict['edit']['parameter'].pop(p.pk)
                                    update_dict['add'][p.pk]['year'].append(pyear)
                                    update_dict['add'][p.pk]['value'].append(convert_units(ureg,v,p_units))
                                elif p.pk in update_dict['add']:
                                    update_dict['add'][p.pk]['year'].append('0')
                                    update_dict['add'][p.pk]['value'].append(v)
                                else:
                                    update_dict['edit']['parameter'][p.pk] = convert_units(ureg,v,p_units)
                            except Exception as e:
                                context['logs'].append(str(i)+'- Tech '+str(row['technology'])+': Column '+f+' '+str(e)+'. Error converting units. Parameter skipped.')
                                continue
                loctech.update(update_dict)
            except Exception as e:
                logger.warning('ERROR in upload_loctechs')
                logger.exception(e)
                context['logs'].append('Unexpected error occured at row '+str(i)+': '+str(e))

        return render(request, "bulkresults.html", context)

    context['logs'].append("No file found")
    return render(request, "bulkresults.html", context)

@csrf_protect
@login_required
def bulk_downloads(request):
    """
    Single endpoint for downloading config template files for a model.

    Parameters:
    model_uuid (uuid): required
    file_list (list): required

    Returns:
    Zip containing one or more files.

    Example:
    GET: /api/bulk_downloads/
    """

    model_uuid = request.GET["model_uuid"]

    model = Model.by_uuid(model_uuid)
    model.handle_edit_access(request.user)

    file_buffs = {}

    # Build location file
    if 'locations' in request.GET['file_list']:
        locations_df = pd.DataFrame.from_records(Location.objects.filter(model=model).values())
        if locations_df.empty:
            locations_df = pd.DataFrame(columns=[f.name for f in Location._meta.get_fields()])
            locations_df.drop(columns=['location_1','location_2','model','created','updated','deleted'],inplace=True)
        else:
            locations_df.drop(columns=['model_id','created','updated','deleted'],inplace=True)
        loc_buff = io.StringIO()
        locations_df.to_csv(loc_buff,index=False)
        file_buffs['locations.csv'] = (loc_buff)

    # Build technology file
    if 'technologies' in request.GET['file_list']:
        techs = Technology.objects.filter(model=model)
        tech_ids = list(techs.values_list('id',
                                          flat=True).distinct())
        param_list = list(Abstract_Tech_Param.objects.all().values_list('parameter__name', flat=True).distinct())
        parameters = Tech_Param.objects.filter(technology_id__in=tech_ids).order_by('-year')
        tech_list = ['id','name','pretty_name','abstract_tech','tag','pretty_tag','calliope_name','description']
        techs_df = pd.DataFrame()
        for t in techs:
            tech_dict = t.__dict__
            tech_dict['calliope_name'] = t.calliope_name
            for p in parameters.filter(technology_id=t.id):
                newcol = False
                pname = p.parameter.name
                if 'costs' in p.parameter.root:
                    try:
                        param_list.remove(pname)
                    except ValueError:
                        pass
                    pname = p.parameter.root+'.'+pname
                    newcol = True
                if p.year:
                    pname+='_'+str(p.year)
                    if pname not in param_list:
                        newcol = True
                if newcol and pname not in param_list:
                    param_list.append(pname)
                if p.timeseries:
                    if p.timeseries_meta is not None:
                        tech_dict[pname] = 'file='+p.timeseries_meta.original_filename+':'+str(p.timeseries_meta.original_timestamp_col)+':'+str(p.timeseries_meta.original_value_col)
                    else:
                        pass
                elif p.raw_value:
                    tech_dict[pname] = p.raw_value
                else:
                    tech_dict[pname] = p.value
            [tech_dict.pop(k) for k in ['abstract_tech_id','_state','model_id','created','updated','deleted']]
            techs_df = techs_df.append(tech_dict, ignore_index=True)
        techs_df = techs_df.rename(columns={'parent':'abstract_tech'})
        # The double for loop keeps the tech fields on the left if there are no records while still allowing for empty paramters
        # to be added on the right after any filled parameters
        for p in list(set(tech_list)-set(techs_df.columns)):
            techs_df[p] = None
        param_list.sort()
        techs_df = techs_df.reindex(columns=[f for f in tech_list+param_list if f in techs_df.columns])
        for p in list(set(param_list)-set(techs_df.columns)):
            techs_df[p] = None
        techs_buff = io.StringIO()
        techs_df.to_csv(techs_buff,index=False)
        file_buffs['techs.csv'] = (techs_buff)

    # Build loc_techs/nodes file
    if 'loc_techs' in request.GET['file_list']:
        loc_techs = Loc_Tech.objects.filter(model=model)
        loc_tech_ids = list(loc_techs.values_list('id',
                                          flat=True).distinct())
        param_list = list(Abstract_Tech_Param.objects.all().values_list('parameter__name', flat=True).distinct())
        parameters = Loc_Tech_Param.objects.filter(loc_tech_id__in=loc_tech_ids).order_by('-year')
        loc_tech_list = ['id','location_1','location_2','technology','tag','calliope_name']
        loc_techs_df = pd.DataFrame()
        for l in loc_techs:
            loc_tech_dict = l.__dict__
            loc_tech_dict['location_1'] = l.location_1.pretty_name
            if l.location_2:
                loc_tech_dict['location_2'] = l.location_2.pretty_name
            loc_tech_dict['technology'] = l.technology.pretty_name
            loc_tech_dict['tag'] = l.technology.pretty_tag
            loc_tech_dict['calliope_name'] = l.technology.calliope_name
            for p in parameters.filter(loc_tech_id=l.id):
                newcol = False
                pname = p.parameter.name
                if 'costs' in p.parameter.root:
                    try:
                        param_list.remove(pname)
                    except ValueError:
                        pass
                    pname = p.parameter.root+'.'+pname
                    newcol = True
                if p.year:
                    pname+='_'+str(p.year)
                    if pname not in param_list:
                        newcol = True
                if newcol and pname not in param_list:
                    param_list.append(pname)
                if p.timeseries:
                    if p.timeseries_meta is not None:
                        if p.timeseries_meta.original_filename:
                            loc_tech_dict[pname] = 'file='+p.timeseries_meta.original_filename+':'+str(p.timeseries_meta.original_timestamp_col)+':'+str(p.timeseries_meta.original_value_col)
                        else:
                            loc_tech_dict[pname] = 'ts='+p.timeseries_meta.name
                    else:
                        pass
                elif p.raw_value:
                    loc_tech_dict[pname] = p.raw_value
                else:
                    loc_tech_dict[pname] = p.value
            [loc_tech_dict.pop(k) for k in ['_state','model_id','created','updated','deleted']]
            loc_techs_df = loc_techs_df.append(loc_tech_dict, ignore_index=True)
        # The double for loop keeps the loc_tech fields on the left if there are no records while still allowing for empty paramters
        # to be added on the right after any filled parameters
        for p in list(set(loc_tech_list)-set(loc_techs_df.columns)):
            loc_techs_df[p] = None
        param_list.sort()
        loc_techs_df = loc_techs_df.reindex(columns=[f for f in loc_tech_list+param_list if f in loc_techs_df.columns])
        for p in list(set(param_list)-set(loc_techs_df.columns)):
            loc_techs_df[p] = None
        loc_techs_buff = io.StringIO()
        loc_techs_df.to_csv(loc_techs_buff,index=False)
        file_buffs['loc_techs.csv'] = (loc_techs_buff)

    zip_buff = io.BytesIO()
    zip_file = zipfile.ZipFile(zip_buff, 'w')
    for buff in file_buffs.keys():
        zip_file.writestr(buff, file_buffs[buff].getvalue())
    zip_file.close()

    response = HttpResponse(zip_buff.getvalue(), content_type="application/x-zip-compressed")
    response['Content-Disposition'] = 'inline; filename='+slugify(model.name)+'_configs.zip'
    return response
