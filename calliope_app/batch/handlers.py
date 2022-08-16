"""Model run handler class

An util class used to run Calliope model in AWS Batch environment.
After a model was built on dashboard, the model information would be 
saved into an api.models.outputs.Run instance, i.e. run.inputs_path.

With the Run instance, we are going to solve the model associated,
and save the model results, plots and logs information into the Run 
intance.
"""
import json
import logging
import os
import sys

import boto3
import django
from django.conf import settings


# Setup django environment before using django models in standalone scripts
def setup_django():
    root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    sys.path.append(root_dir)
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "calliope_app.settings.local")
    
    # Ensure Django logfile before setup
    logfile = "/opt/python/log/django.log"
    os.makedirs(os.path.dirname(logfile), exist_ok=True)
    if not os.path.exists(logfile):
        with open(logfile, "w") as f:
            pass
    
    django.setup()

setup_django()

from api.engage import aws_ses_configured
from api.models.outputs import Run
from api.tasks import task_status as run_status
from api.tasks import CalliopeModelRunTask, NOTIFICATION_TIME_INTERVAL, run_model
from api.utils import zip_folder
from taskmeta.models import batch_task_status

logger = logging.getLogger(__name__)


class ModelRunExecutor:
    """A util class for manage model run associated to Django model"""
    
    def __init__(self, run_id, user_id):
        """Initialize the handler class

        Parameters
        ----------
        run_id : int
            The run instance id, aka, run.id
        user_id : int
            The user instance id, aka, user.id
        """
        self.run_id = run_id
        self.run = self._get_run_instance(run_id)
        self.path_base = self._get_path_base(run_id)
        self.user_id = user_id
    
    def _get_path_base(self, run_id):
        run = self._get_run_instance(run_id)
        return os.path.dirname(run.inputs_path)

    def _get_run_instance(self, run_id):
        try:
            run = Run.objects.get(id=run_id)
        except Run.DoesNotExist as exc:
            logger.exception(exc)
            raise
        return run

    @property
    def inputs_path(self):
        return os.path.join(self.path_base, "inputs")
    
    @property
    def model_path(self):
        return os.path.join(self.inputs_path, "model.yaml")

    @property
    def logs_path(self):
        return os.path.join(self.path_base, "logs.html")

    @property
    def outputs_path(self):
        return os.path.join(self.path_base, "outputs", "model_outputs")

    @property
    def outputs_zip(self):
        return self.outputs_path + ".zip"

    @property
    def outputs_key(self):
        return self.outputs_zip.replace("/data/", "engage/")

    @property
    def plots_path(self):
        return os.path.join(self.path_base, "plots.html")

    def solve_model(self):
        """Solve Calliope model and handle success/failure cases"""
        self._ensure_logs_file()
        try:
            run_model(
                run_id=self.run_id,
                model_path=self.model_path,
                user_id=self.user_id
            )
            self._handle_on_success()
        except Exception as exc:
            self._handle_on_failure(exc)
            return False
        return True

    def _ensure_logs_file(self):
        if os.path.exists(self.logs_path):
            return
    
        with open(self.logs_path, "w") as f:
            pass

    def _handle_on_failure(self, exc):
        """Handle run instance and logs when model run failed"""
        # Update Run instance
        self.run.status = run_status.FAILURE
        self.run.message = str(exc)
        self.run.outputs_path = ""
        self.run.plots_path = ""
        self.run.logs_path = self.logs_path
        self.run.save()

        self.run.batch_job.status = batch_task_status.FAILED
        self.run.batch_job.result = ""
        self.run.batch_job.traceback = str(exc)
        self.run.batch_job.save()
        
        # Send notifications via email to user/admin.
        if self._get_elasped_run_time(self.run) >= NOTIFICATION_TIME_INTERVAL:
            notification_enabled = True
        else:
            notification_enabled = False

        if aws_ses_configured() and notification_enabled:
            try:
                CalliopeModelRunTask.notify_user(self.run, self.user_id, success=False, exc=exc)
                CalliopeModelRunTask.notify_admin(self.run, self.user_id, None, success=False, exc=exc)
            except Exception as exc:
                pass
    
    def _get_elasped_run_time(self, run):
        """Get model run time in minutes"""
        elasped_time = run.updated - run.created
        return elasped_time.total_seconds() / 60
    
    def _handle_on_success(self):
        """Handle run instance and exports when model run success"""
        # Update run instance with model run information
        self.run.logs_path = self.logs_path
        self.run.outputs_path = self.outputs_path
        if os.path.exists(self.outputs_path):
            self.run.status = run_status.SUCCESS
        self.run.save()
        
        # Upload results to S3 bucekt if configured
        if not settings.AWS_S3_BUCKET_NAME:
            return
        client = boto3.client(service_name="s3", region_name="us-west-2")
        zip_file = zip_folder(self.outputs_path)
        client.upload_file(zip_file, settings.AWS_S3_BUCKET_NAME, self.outputs_key)
        self.run.outputs_key = self.outputs_key
        self.run.save()

        self.run.batch_job.status = batch_task_status.SUCCEEDED
        self.run.batch_job.result = json.dumps({
            "logs": self.logs_path,
            "outputs": self.outputs_path,
            "plots": self.plots_path
        }, indent=2)
        self.run.batch_job.traceback = ""
        self.run.batch_job.save()
