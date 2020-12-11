"""
Celery task module
"""
import os
import shutil

import boto3
import botocore
import pandas as pd
import numpy as np
from dateutil.parser import parse as date_parse

from celery import Task
from celery.exceptions import SoftTimeLimitExceeded
from calliope import Model as CalliopeModel
from calliope_app.celery import app
from django.contrib.auth.models import User
from django.conf import settings
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils.safestring import mark_safe

from api.engage import aws_ses_configured
from api.models.configuration import Model, Scenario, Scenario_Loc_Tech, \
    Tech_Param, Loc_Tech_Param, Timeseries_Meta, User_File
from api.models.outputs import Run
from api.utils import list_to_yaml, load_timeseries_from_csv, get_model_logger, \
    zip_folder
from api.calliope_utils import get_model_yaml_set, get_location_meta_yaml_set
from api.calliope_utils import get_techs_yaml_set, get_loc_techs_yaml_set


NOTIFICATION_TIME_INTERVAL = 20 # Minutes


class ModelTaskStatus(object):
    """
    Task status
    """
    BUILDING = "BUILDING"
    BUILT = "BUILT"
    QUEUED = "QUEUED"
    RUNNING = "RUNNING"
    SUCCESS = "SUCCESS"
    FAILURE = "FAILURE"


task_status = ModelTaskStatus


class CalliopeTimeseriesUploadTask(Task):
    """
    A celery task class for handling success/failure status
    """

    def on_failure(self, exc, task_id, args, kwargs, einfo):
        """
        On failure, delete the new meta
        """
        timeout_message = "Timeout! TimeLimit=%s seconds." % self.time_limit
        exc = timeout_message if str(exc) == "SoftTimeLimitExceeded()" else exc

        new_meta = Timeseries_Meta.objects.get(id=kwargs["timeseries_meta_id"])
        new_meta.is_uploading = False
        new_meta.failure = True
        new_meta.message = str(exc)
        new_meta.save()

    def on_success(self, retval, task_id, args, kwargs):
        """
        On success, set is_uploading to be False.
        """
        new_meta = Timeseries_Meta.objects.get(id=kwargs["timeseries_meta_id"])
        new_meta.is_uploading = False
        new_meta.save()


@app.task(
    base=CalliopeTimeseriesUploadTask,
    queue="short_queue",
    soft_time_limit=3600 - 60,
    time_limit=3600,
    ignore_result=True
)
def upload_ts(model_uuid, timeseries_meta_id, file_id,
              timestamp_col, value_col, has_header, *args, **kwargs):
    """
    A celery task for handling timeseries data upload, which may take
    a long time, so to avoid https request timeout.
    """
    model = Model.objects.get(uuid=model_uuid)
    file_record = User_File.objects.filter(model=model, id=file_id)
    filename = file_record.first().filename

    new_meta = Timeseries_Meta.objects.get(id=timeseries_meta_id)

    ts = load_timeseries_from_csv(
        filename, timestamp_col, value_col, has_header)

    directory = "{}/timeseries".format(settings.DATA_STORAGE)
    if not os.path.exists(directory):
        os.makedirs(directory)
    fname = "{}/{}.csv".format(directory, new_meta.file_uuid)
    ts.to_csv(fname)


class CalliopeModelBuildTask(Task):
    """
    A celery task class for building calliope model.
    """

    def on_failure(self, exc, task_id, args, kwargs, einfo):
        """
        On failure, write failure exceptions to log,
        and mark the task status to failure.
        """
        timeout_message = "Build Timeout! TimeLimit=%s seconds." % self.time_limit
        exc = timeout_message if str(exc) == "SoftTimeLimitExceeded()" else exc

        # create model build failure log
        log_file = os.path.join(
            os.path.dirname(kwargs["inputs_path"]), "logs.html")
        logger = get_model_logger(log_file)
        logger.error("{!r}".format(str(exc)))
        save_logs = logger.handlers[0].baseFilename

        # Update the status of run in db
        run = Run.objects.get(id=kwargs["run_id"])
        run.status = task_status.FAILURE
        run.message = exc
        run.logs_path = save_logs
        run.save()

    def on_success(self, retval, task_id, args, kwargs):
        """
        On success, mark the task status to success.
        """
        run = Run.objects.get(id=kwargs["run_id"])
        run.status = task_status.BUILT
        run.inputs_path = retval
        run.save()


@app.task(
    base=CalliopeModelBuildTask,
    queue="short_queue",
    soft_time_limit=3600-60,
    time_limit=3600,
    ignore_result=True
)
def build_model(inputs_path, run_id, model_uuid, scenario_id,
                start_date, end_date, *args, **kwargs):
    """
    Build Calliope model in an asynchronous way using Celery.
    For more details, please refer to...
    https://calliope.readthedocs.io/en/stable/user/building.html

    :param inputs_path: str, the directory in which to build the model
    :param run_id: int, run instance id
    :param model_uuid: str, uuid4 string id of calliope model
    :param scenario_id: int, the id the scenario instance
    :param start_date: str, the start date of timeseries data
    :param end_date: str, the end date of timeseries data
    :param args:
    :param kwargs:
    :return:
    """
    run = Run.objects.get(id=run_id)
    run.status = task_status.BUILDING
    run.save()

    # model and scenario instances
    model = Model.objects.get(uuid=model_uuid)
    scenario = Scenario.objects.get(id=scenario_id)

    build_model_yaml(scenario_id, start_date, inputs_path)
    build_model_csv(model, scenario, start_date, end_date, inputs_path)

    return inputs_path


def build_model_yaml(scenario_id, start_date, inputs_path):

    scenario_id = int(scenario_id)
    year = date_parse(start_date).year

    # model.yaml
    model_yaml_set = get_model_yaml_set(scenario_id, year)
    list_to_yaml(model_yaml_set, os.path.join(inputs_path, "model.yaml"))

    # techs.yaml
    techs_yaml_set = get_techs_yaml_set(scenario_id, year)
    list_to_yaml(techs_yaml_set, os.path.join(inputs_path, "techs.yaml"))

    # locations.yaml
    loc_techs_yaml_set = get_loc_techs_yaml_set(scenario_id, year)
    location_coord_yaml_set = get_location_meta_yaml_set(scenario_id)
    list_to_yaml(loc_techs_yaml_set + location_coord_yaml_set,
                 os.path.join(inputs_path, "locations.yaml"))


def build_model_csv(model, scenario, start_date, end_date, inputs_path):
    # timeseries: *.csv
    loc_techs = Scenario_Loc_Tech.objects.filter(
        model=model, scenario=scenario)
    tech_ids = list(set(
        loc_techs.values_list("loc_tech__technology_id", flat=True)))
    loc_tech_ids = list(set(loc_techs.values_list("loc_tech_id", flat=True)))

    tech_ts = Tech_Param.objects.filter(
        model=model, timeseries=True, technology_id__in=tech_ids)
    loc_tech_ts = Loc_Tech_Param.objects.filter(
        model=model, timeseries=True, loc_tech_id__in=loc_tech_ids)

    for ts in list(tech_ts) + list(loc_tech_ts):
        timeseries_meta_id = ts.timeseries_meta_id
        parameter_name = ts.parameter.name
        try:
            location_1_name = ts.loc_tech.location_1.name
            technology_name = ts.loc_tech.technology.calliope_name
            if not ts.loc_tech.location_2:
                filename = os.path.join(
                    inputs_path, "{}--{}--{}.csv".format(
                        location_1_name, technology_name,
                        parameter_name))
            else:
                location_2_name = ts.loc_tech.location_2.name
                filename = os.path.join(inputs_path,
                                        "{},{}--{}--{}.csv".format(
                                            location_1_name, location_2_name,
                                            technology_name,
                                            parameter_name))
        except Exception as e:
            print(e)
            technology_name = ts.technology.calliope_name
            filename = os.path.join(
                inputs_path, "{}--{}.csv".format(
                    technology_name, parameter_name))
        timeseries_meta = Timeseries_Meta.objects.filter(
            id=timeseries_meta_id).first()
        if timeseries_meta is not None:
            directory = "{}/timeseries".format(settings.DATA_STORAGE)
            input_fname = "{}/{}.csv".format(
                directory, timeseries_meta.file_uuid)
            timeseries = get_timeseries_data(input_fname, start_date, end_date)
            timeseries.to_csv(filename)


def get_timeseries_data(filename, start_date, end_date):
    """ Load up timeseries data into a DataFrame for an intra-year period. """
    timeseries = pd.read_csv(filename, parse_dates=[0])
    timeseries.index = pd.to_datetime(timeseries.datetime)
    del (timeseries['datetime'])
    timeseries.columns = ["value"]
    start_date = pd.to_datetime(start_date)
    end_date = pd.to_datetime(end_date)

    # Grab available year's data
    mask = (timeseries.index >= start_date) & \
           (timeseries.index <= end_date)
    subset = timeseries[mask]

    # If year is not available: grad latest (or nearest) available data year
    if len(subset) == 0:
        year = start_date.year
        years = np.array(timeseries.index.year.unique())

        latest = years[years < year]
        if latest:
            recent_year = latest.max()
        else:
            recent_year = years[years > year].min()
        start_date = start_date.replace(year=recent_year)
        end_date = end_date.replace(year=recent_year)

        mask = (timeseries.index >= start_date) & \
               (timeseries.index <= end_date)
        subset = timeseries[mask]
        subset.index = subset.index.map(lambda t: t.replace(year=year))

    return subset


class CalliopeModelRunTask(Task):
    """
    A celery task class for calliope model run.
    """

    clean_msg_dict = {
        "list index out of range":
            ("One or more of the timeseries do not span "
             "the selected run period"),
        "index 0 is out of bounds for axis 0 with size":
            ("One or more of the timeseries do not span "
             "the selected run period"),
        "techs":
            "No nodes have been selected for this scenario",
        "'str' object has no attribute 'keys'":
            "Group share constraint is not valid json",
        "'ConcreteModel' object has no attribute 'loc_tech_carriers_prod'":
            "There are no supply technologies configured",
        "does not exist":
            "A timeseries has not been selected for a timeseries parameter"
    }

    def notify_user(self, run, user_id, success=True, exc=None):
        """Send notification to user"""
        # Get user
        try:
            user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            user = None
        user_name = user.first_name if user and user.first_name.strip() else "Engage User"

        # Create message
        if success:
            context = {
                "user_name": user_name,
                "model_name": run.model.name,
                "model_uuid": run.model.get_uuid(),
            }
            message = render_to_string("notifications/notify_user_on_run_success.txt", context)
        else:
            context = {
                "user_name": user_name,
                "model_name": run.model.name,
                "model_uuid": run.model.get_uuid(),
                "error_message": "Unknown Error" if not exc else mark_safe(str(exc))
            }
            message = render_to_string("notifications/notify_user_on_run_failure.txt", context)

        # Send email
        recipient_list = [] if not user else [user.email]
        if not recipient_list:
            return
        send_mail(
            subject="NREL ENGAGE NOTIFICATION",
            message=message,
            from_email=settings.AWS_SES_FROM_EMAIL,
            recipient_list=recipient_list
        )

    def notify_admin(self, run, user_id, task_id, success=False, exc=None):
        """Send notification to admin"""
        if success:
            return

        # Get user
        try:
            user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            user = None

        if user:
            user_name = user.first_name + " " + user.last_name + f"[{user.email}]"
        else:
            user_name = "Anonymous User"

        # Create message
        context = {
            "user_name": user_name,
            "model_name": run.model.name,
            "error_message": "Unknown Error" if not exc else mark_safe(str(exc)),
            "task_id": task_id,
        }
        message = render_to_string("notifications/notify_admin_on_run_failure.txt", context)

        # Send email
        recipient_list = [admin.email for admin in User.objects.filter(is_superuser=True)]
        if not recipient_list:
            return
        send_mail(
            subject="NREL ENGAGE NOTIFICATION",
            message=message,
            from_email=settings.AWS_SES_FROM_EMAIL,
            recipient_list=recipient_list
        )
    
    def get_elasped_run_time(self, run):
        """Get model run time in minutes"""
        elasped_time = run.updated - run.created
        return elasped_time.total_seconds() / 60

    def on_failure(self, exc, task_id, args, kwargs, einfo):
        """
        On failure, write the storage path of logs to database.
        """
        # create failure log
        log_file = os.path.join(os.path.dirname(os.path.dirname(
            kwargs["model_path"])), "logs.html")
        logger = get_model_logger(log_file)

        timeout_message = "Run Timeout! TimeLimit=%s seconds." % self.time_limit
        exc = timeout_message if str(exc) == "SoftTimeLimitExceeded()" else exc
        logger.error("{!r}".format(str(exc)))

        # Add pretty error to the log
        for key in self.clean_msg_dict:
            if key in str(exc):
                exc = self.clean_msg_dict[key]
                logger.error("{!r}".format(exc))
        save_logs = logger.handlers[0].baseFilename

        # Update the status of run in db
        run = Run.objects.get(id=kwargs["run_id"])
        run.status = task_status.FAILURE
        run.message = exc
        run.outputs_path = ""
        run.plots_path = ""
        run.logs_path = save_logs
        run.save()
        
        # Send failure notification to user
        if self.get_elasped_run_time(run) >= NOTIFICATION_TIME_INTERVAL:
            notification_enabled = True
        else:
            notification_enabled = False
        
        if aws_ses_configured() and notification_enabled:
            try:
                self.notify_user(run, kwargs["user_id"], success=False, exc=exc)
                self.notify_admin(run, kwargs["user_id"], task_id, success=False, exc=exc)
            except Exception as err:
                pass

    def on_success(self, retval, task_id, args, kwargs):
        """
        On success, write the storage path of logs,
        outputs and plots to database.
        """
        # Update run instance in database
        run = Run.objects.get(id=retval["run_id"])
        run.status = task_status.SUCCESS
        run.logs_path = retval["save_logs"]
        run.outputs_path = retval["save_outputs"]
        run.plots_path = retval["save_plots"]
        run.save()

        # Upload model_outputs to S3
        if not settings.AWS_S3_BUCKET_NAME:
            return

        client = boto3.client(
            service_name="s3",
            aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY
        )
        zip_file = zip_folder(retval["save_outputs"])
        key = "engage" + zip_file
        client.upload_file(zip_file, settings.AWS_S3_BUCKET_NAME, key)


@app.task(
    base=CalliopeModelRunTask,
    queue="long_queue",
    soft_time_limit=24*3600-180,
    time_limit=24*3600
)
def run_model(run_id, model_path, user_id, *args, **kwargs):
    """
    Run calliope model using asynchronous way with Celery.
    Please refer to
    https://calliope.readthedocs.io/en/stable/_modules/calliope/core/model.html#Model

    Parameters
    ----------
    run_id: int, the id of api.models.Run instance.
    model_path: str, the path to the model yaml file.
    user_id: int, the user id of current task.

    Returns
    -------
    dict, the outputs of model run, including netcdf, csv and plots.

    """
    # Logging Config
    log_file = os.path.join(os.path.dirname(
        os.path.dirname(model_path)), "logs.html")
    logger = get_model_logger(log_file)

    # Update run status
    run = Run.objects.get(id=run_id)
    run.status = task_status.RUNNING
    run.save()

    # Model run
    model = CalliopeModel(config=model_path, *args, **kwargs)
    model.run()
    logger.info("Backend: Model runs successfully!")

    # Model outputs in csv
    base_path = os.path.dirname(os.path.dirname(model_path))
    logger.info("Backend: Saving model results...")
    try:
        if not os.path.exists(base_path + "/outputs"):
            os.makedirs(base_path + "/outputs", exist_ok=True)
        save_outputs = os.path.join(base_path, "outputs/model_outputs")
        if os.path.exists(save_outputs):
            shutil.rmtree(save_outputs)
        model.to_csv(save_outputs)
        logger.info("Backend: Model outputs was saved.")
    except Exception as e:
        logger.error("Backend: Failed to save model outputs.")
        logger.error(str(e))
        save_outputs = ""

    # Model plots in html
    try:
        if not os.path.exists(base_path + "/plots"):
            os.makedirs(base_path + "/plots", exist_ok=True)
        save_plots = os.path.join(base_path, "plots/model_plots.html")
        if os.path.exists(save_plots):
            os.remove(save_plots)
        model.plot.summary(to_file=save_plots)
        logger.info("Backend: Model plots was saved.")
    except Exception as e:
        logger.error("Backend: Failed to save model plots.")
        logger.error(str(e))
        save_plots = ""

    # Model logs in plain text
    save_logs = logger.handlers[0].baseFilename

    return {
        "run_id": run_id,
        "save_outputs": save_outputs,
        "save_plots": save_plots,
        "save_logs": save_logs
    }
