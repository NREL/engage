import datetime
import os

from celery import Task
from django.conf import settings

from api.models.configuration import Job_Meta
from api.tasks import task_status
from calliope_app.celery import app
from geophires.v2 import GeophiresParams, Geophires

class GeophiresTask(Task):
    """
    A celery task class for executing a geophires job.
    """
    def on_success(self, retval, task_id, args, kwargs):
        """
        On success, mark the task status to success.
        """
        job_meta = Job_Meta.objects.get(id=kwargs["job_meta_id"])
        job_meta.status = task_status.SUCCESS
        job_meta.outputs = retval
        job_meta.save()

    def on_failure(self, exc, task_id, args, kwargs, einfo):
        """
        On failure, write failure exceptions to log,
        and mark the task status to failure.
        """
        timeout_message = "Job Timeout! TimeLimit=%s seconds." % self.time_limit
        exc = timeout_message if str(exc) == "SoftTimeLimitExceeded()" else exc

        # Update the status of run in db
        job_meta = Job_Meta.objects.get(id=kwargs["job_meta_id"])
        job_meta.status = task_status.FAILURE
        job_meta.message = exc
        job_meta.save()


@app.task(
    base=GeophiresTask,
    queue="short_queue",
    soft_time_limit=600-6,
    ime_limit=600,
    ignore_result=True
)
def run_geophires(job_meta_id, plant, params, *args, **kwargs):
    """Run geophires task

    Parameters
    ----------
    plant : str
        The plant type
    params : dict
        The geophires parameters
    """
    ## Update job meta
    job_meta = Job_Meta.objects.get(id=job_meta_id)
    job_meta.status = task_status.RUNNING
    job_meta.save()

    ## Geophires job run
    input_params = GeophiresParams(**params)

    timestamp = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
    result_file = os.path.join(settings.DATA_STORAGE, "geophires", f"{job_meta_id}__{plant}__{timestamp}.csv")

    geophiers = Geophires(plant)
    output_params, output_file = geophiers.run(input_params=input_params, output_file=result_file)

    return {
        "plant": plant,
        "output_params": output_params,
        "output_file": output_file
    }
