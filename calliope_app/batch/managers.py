import logging
import boto3
from abc import ABC, abstractmethod

from django.conf import settings

logger = logging.getLogger(__name__)


class AWSBatchClient(ABC):

    def __init__(self):
        self.client =  boto3.client("batch", region_name=settings.AWS_REGION_NAME)
    
    @abstractmethod
    def get_job_definition(self):
        """Get the job definition name"""


class AWSBatchJobManager(AWSBatchClient):
    """
    AWS Batch job manager for scheduling Engage model runs.
    """
    def __init__(self, compute_environment):
        """Initialize the batch job manager

        Parameters
        ----------
        compute_environment : object | ComputeEnvironment
            The name of Batch compute environment
        """
        super().__init__()
        self.compute_environment = compute_environment
    
    def get_job_definition(self):
        """Store job definition name from compute environment alias"""
        return self.compute_environment.alias
    
    def submit_job(self, job):
        response = self.client.submit_job(
            jobName=job["name"],
            jobQueue=settings.AWS_BATCH_JOB_QUEUE,
            jobDefinition=job["definition"],
            containerOverrides={"command": job["command"]}
        )
        logger.info("Engage batch job submitted - %s", job["name"])
        return response

    def generate_job_message(self, run_id, user_id):
        job = {
            "name": f"Engage-Model-Run-UserId-{user_id}-RunId-{run_id}",
            "command": [
                "engage", "solve-model",
                "--run-id", str(run_id),
                "--user-id", str(user_id)
            ],
            "definition": self.get_job_definition()
        }
        return job

    def compute_environment_in_use(self):
        """
        To make sure only one job queued with given job definition
        """
        job_definition = self.get_job_definition()

        uncomplete_status = ["SUBMITTED", "PENDING", "RUNNABLE", "STARTING", "RUNNING"]
        for job_status in uncomplete_status:
            response = self.client.list_jobs(
                jobQueue=settings.AWS_BATCH_JOB_QUEUE,
                jobStatus=job_status
            )
            for job in response["jobSummaryList"]:
                if job["jobDefinition"] == job_definition:
                    return True
        return False
