"""
Celery task module
"""
import os
import shutil

import boto3
import botocore
import pandas as pd
import numpy as np
import datetime
import yaml
from dateutil.parser import parse as date_parse

from celery import Task
from celery.exceptions import SoftTimeLimitExceeded
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
from api.utils import list_to_yaml, load_timeseries_from_csv, \
    get_model_logger, zip_folder
from api.calliope_utils import get_model_yaml_set, get_location_meta_yaml_set
from api.calliope_utils import get_techs_yaml_set, get_loc_techs_yaml_set
from api.calliope_utils import run_basic, run_clustered


NOTIFICATION_TIME_INTERVAL = 20  # Minutes


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


class CopyModelTask(Task):
    """
    A celery task class for handling success/failure status
    """

    def on_failure(self, exc, task_id, args, kwargs, einfo):
        """
        On failure, delete the new model
        """
        model = Model.objects.get(id=kwargs["dst_model_id"])
        model.delete()

    def on_success(self, retval, task_id, args, kwargs):
        """
        On success, set is_uploading to be False.
        """
        model = Model.objects.get(id=kwargs["dst_model_id"])
        model.is_uploading = False
        model.save()


@app.task(
    base=CopyModelTask,
    queue="short_queue",
    soft_time_limit=3600 - 60,
    time_limit=3600,
    ignore_result=True
)
def copy_model(src_model_id, dst_model_id, user_id, *args, **kwargs):
    """
    A celery task for handling model duplication
    """
    src_model = Model.objects.get(id=src_model_id)
    dst_model = Model.objects.get(id=dst_model_id)
    user = User.objects.get(id=user_id)
    src_model.duplicate(dst_model, user)


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
    build_model_csv(model, scenario, start_date, end_date, inputs_path, run.timestep)

    return inputs_path


def build_model_yaml(scenario_id, start_date, inputs_path):

    scenario_id = int(scenario_id)
    year = date_parse(start_date).year

    # model.yaml
    model_yaml_set = get_model_yaml_set(scenario_id, year)
    with open(os.path.join(inputs_path, "model.yaml"), 'w') as outfile:
        yaml.dump(model_yaml_set, outfile, default_flow_style=False)

    # techs.yaml
    techs_yaml_set = get_techs_yaml_set(scenario_id, year)
    with open(os.path.join(inputs_path, "techs.yaml"), 'w') as outfile:
        yaml.dump(techs_yaml_set, outfile, default_flow_style=False)

    # locations.yaml
    loc_techs_yaml_set = get_loc_techs_yaml_set(scenario_id, year)
    location_yaml_set = get_location_meta_yaml_set(scenario_id, loc_techs_yaml_set)
    with open(os.path.join(inputs_path, "locations.yaml"), 'w') as outfile:
        yaml.dump(location_yaml_set, outfile, default_flow_style=False)


def build_model_csv(model, scenario, start_date, end_date, inputs_path, timesteps):
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
        parameter_root = ts.parameter.root.replace('.','-')
        if ts in loc_tech_ts:
            location_1_name = ts.loc_tech.location_1.name
            technology_name = ts.loc_tech.technology.calliope_name
            if not ts.loc_tech.location_2:
                filename = os.path.join(
                    inputs_path, "{}--{}--{}-{}.csv".format(
                        location_1_name, technology_name,
                        parameter_root, parameter_name))
            else:
                location_2_name = ts.loc_tech.location_2.name
                filename = os.path.join(inputs_path,
                                        "{},{}--{}--{}-{}.csv".format(
                                            location_1_name, location_2_name,
                                            technology_name, parameter_root,
                                            parameter_name))
        elif ts in tech_ts:
            technology_name = ts.technology.calliope_name
            filename = os.path.join(
                inputs_path, "{}--{}-{}.csv".format(
                    technology_name, parameter_root, parameter_name))
        timeseries_meta = Timeseries_Meta.objects.filter(
            id=timeseries_meta_id).first()
        if timeseries_meta is not None:
            directory = "{}/timeseries".format(settings.DATA_STORAGE)
            input_fname = "{}/{}.csv".format(
                directory, timeseries_meta.file_uuid)
            timeseries = get_timeseries_data(input_fname, start_date, end_date, timesteps)
            timeseries.to_csv(filename)


def get_timeseries_data(filename, start_date, end_date, timesteps):
    """ Load up timeseries data into a DataFrame for an intra-year period. """
    timeseries = pd.read_csv(filename, parse_dates=[0])
    timeseries.index = pd.DatetimeIndex(timeseries.datetime).tz_localize(None)
    del (timeseries['datetime'])
    timeseries.columns = ["value"]
    start_date = pd.to_datetime(start_date)
    end_date = pd.to_datetime(end_date)
    year = start_date.year

    # Grab available year's data
    mask = (timeseries.index >= start_date) & \
           (timeseries.index <= end_date)
    subset = timeseries[mask]

    # If year is not available: grab latest (or nearest) available data year
    if len(subset) == 0:
        years = np.array(timeseries.index.year.unique())
        latest = years[years < year]
        if len(latest) > 0:
            recent_year = latest.max()
        else:
            recent_year = years[years > year].min()
        start_date2 = start_date.replace(year=recent_year)
        end_date2 = end_date.replace(year=recent_year)
        mask = (timeseries.index >= start_date2) & \
               (timeseries.index <= end_date2)
        subset = timeseries[mask]

    # Remove extra leap year days and reset correct year
    feb_29_mask = (subset.index.month == 2) & (subset.index.day == 29)
    subset = subset[~feb_29_mask]
    subset.index = subset.index.map(lambda t: t.replace(year=year))

    # Determine offset difference and resample to run's timesteps
    diffs = (subset.index[1:]-subset.index[:-1])
    min_delta = diffs.min()
    subset_freq = start_date+min_delta
    target_freq = start_date+pd.tseries.frequencies.to_offset(timesteps)
    if subset_freq<target_freq:
        subset = subset.resample(rule=timesteps).mean()
    elif subset_freq>target_freq:
        subset = subset.resample(rule=timesteps).interpolate()

    # Fill Missing Timesteps w/ 0
    idx = pd.period_range(start_date, end_date, freq=timesteps).to_timestamp()
    subset = subset.reindex(idx, fill_value=0)

    # Leap Year Handling (Fill w/ Feb 28th)
    if year % 4 == 0:
        feb_28_mask = (subset.index.month == 2) & (subset.index.day == 28)
        feb_29_mask = (subset.index.month == 2) & (subset.index.day == 29)
        feb_28 = subset.loc[feb_28_mask, 'value'].values
        feb_29 = subset.loc[feb_29_mask, 'value'].values
        if ((len(feb_29) > 0) & (len(feb_28) > 0)):
            subset.loc[feb_29_mask, 'value'] = feb_28

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
            "Scenario settings constraint does not have valid JSON format",
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
        run.logs_path = retval["save_logs"]
        run.outputs_path = retval["save_outputs"]
        results = os.path.join(run.outputs_path, 'results_carrier_prod.csv')
        if os.path.exists(results):
            run.status = task_status.SUCCESS
        else:
            run.status = task_status.FAILURE
        run.save()

        # Upload model_outputs to S3
        if not settings.AWS_S3_BUCKET_NAME:
            return

        client = boto3.client(
            service_name="s3",
            region_name="us-west-2",
            aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY
        )
        zip_file = zip_folder(retval["save_outputs"])
        key = "engage" + zip_file.replace(settings.DATA_STORAGE, '')
        client.upload_file(zip_file, settings.AWS_S3_BUCKET_NAME, key)

        run.outputs_key = key
        run.save()


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

    # Init
    subset_time = run.subset_time.split(' to ')
    st = pd.to_datetime(subset_time[0])
    et = pd.to_datetime(subset_time[1]) + pd.DateOffset(hours=23)
    idx = pd.date_range(start=st, end=et, freq='h')

    # Model run
    if run.cluster and len(idx) > (24 * 14):
        # Cap the number of representative days to 14 (temporary solution)
        logger.info('Running clustered optimization...')
        condition = run_clustered(model_path, idx, logger)
    else:
        logger.info('Running basic optimization...')
        condition = run_basic(model_path, logger)
    logger.info("Backend: Model runs complete, STATUS: {}".format(condition))

    # Model outputs
    base_path = os.path.dirname(os.path.dirname(model_path))
    save_outputs = os.path.join(base_path, "outputs/model_outputs")

    # Model logs in plain text
    save_logs = logger.handlers[0].baseFilename

    return {
        "run_id": run_id,
        "save_outputs": save_outputs,
        "save_logs": save_logs
    }


class CalliopeTimeseriesUploadTask(Task):
    """
    A celery task class for handling success/failure status
    """

    def on_failure(self, exc, task_id, args, kwargs, einfo):
        pass

    def on_success(self, retval, task_id, args, kwargs):
        pass


@app.task(
    base=CalliopeTimeseriesUploadTask,
    queue="long_queue",
    soft_time_limit=(48 * 3600 - 180),
    time_limit=(48 * 3600),
    ignore_result=True
)
def upgrade_066(*args, **kwargs):
    """
    A celery task for migrating output data to 066 format with headers.
    """
    runs = Run.objects.exclude(status='SUCCESS')
    runs.update(calliope_066_upgraded=True)
    runs = Run.objects.filter(status='SUCCESS')
    for r, run in enumerate(runs):
        if run.calliope_066_upgraded:
            continue
        run.calliope_066_errors = ""
        try:
            outputs_path = run.outputs_path
            if not outputs_path:
                run.calliope_066_upgraded = True
                run.save()
                continue
            # --- BACKUP
            backup = outputs_path + '_backup'
            if not os.path.exists(backup):
                shutil.copytree(outputs_path, backup)
            # --- META
            # Locations
            locs = list(pd.read_csv(
                os.path.join(backup, 'inputs_loc_coordinates.csv'),
                header=None)[1].unique())
            if 'locs' in locs:
                run.calliope_066_upgraded = True
                run.save()
                continue
            # Technologies
            techs = list(pd.read_csv(
                os.path.join(backup, 'inputs_names.csv'),
                header=None)[0].unique())
            techs += list(pd.read_csv(
                os.path.join(backup, 'inputs_lookup_remotes.csv'),
                header=None)[1].unique())
            # Carriers
            carriers = pd.read_csv(
                os.path.join(backup, 'inputs_lookup_loc_carriers.csv'),
                header=None)
            index = 1 if set(carriers[0].unique()).issubset(locs) else 0
            carriers = list(carriers[index].unique())
            # --- UPDATE
            files = os.listdir(backup)
            for file in files:
                try:
                    src = os.path.join(backup, file)
                    dst = os.path.join(outputs_path, file)
                    try:
                        d = pd.read_csv(src, header=None)
                    except pd.errors.EmptyDataError:
                        continue
                    # Metric
                    if 'inputs' in file:
                        metric = file.split('inputs_')[1][:-4]
                    else:
                        metric = file.split('results_')[1][:-4]
                    try:
                        int(metric[-2:])
                        metric = metric[:-3]
                    except Exception:
                        pass
                    # Update Each Column Header
                    columns = list(d.columns)
                    for i, col in enumerate(columns):
                        values = list(d[col].unique())
                        if len(values) == 1 and 'monetary' in values:
                            columns[i] = 'costs'
                        elif set(['in', 'out']).issubset(values):
                            columns[i] = 'carrier_tiers'
                        elif set(values).issubset(['lat', 'lon']):
                            columns[i] = 'coordinates'
                        elif set(values).issubset(locs):
                            columns[i] = 'locs'
                        elif set(values).issubset(carriers):
                            columns[i] = 'carriers'
                        elif set(values).issubset(techs):
                            columns[i] = 'techs'
                        elif 'group_share' in metric and i == 1:
                            columns[i] = 'techlists'
                        else:
                            try:
                                datetime.datetime.strptime(values[0],
                                                           '%Y-%m-%d %H:%M:%S')
                                if metric == 'max_demand_timesteps':
                                    columns[i] = metric
                                else:
                                    columns[i] = 'timesteps'
                            except Exception:
                                try:
                                    datetime.datetime.strptime(values[0],
                                                               '%Y-%m-%d')
                                    columns[i] = 'datesteps'
                                except Exception:
                                    try:
                                        if 'cluster' in metric and sorted(values) == list(range(np.max(values) + 1)):
                                            columns[i] = 'cluster'
                                        else:
                                            raise
                                    except Exception:
                                        columns[i] = metric
                    if 'cluster' in columns and metric not in columns:
                        i = columns.index('cluster')
                        columns[i] = metric
                    d.columns = columns
                    if len(columns) != len(set(columns)):
                        print('\n\n', r, file, '\n')
                        print(d.head())
                    d.to_csv(dst, index=False)
                except Exception as e:
                    error = "ERROR ({}): {} | ".format(file, str(e))
                    run.calliope_066_errors += error
                    pass
        except Exception as e:
            error = "ERROR: {} | ".format(str(e))
            run.calliope_066_errors += error
            pass
        if run.calliope_066_errors == "":
            run.calliope_066_upgraded = True
        run.save()
