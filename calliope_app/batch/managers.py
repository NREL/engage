import json
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
        """Store job definition name from compute environment"""
        return self.compute_environment.full_name
    
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
        command = [
            "engage", "solve-model",
            "--run-id", str(run_id),
            "--user-id", str(user_id)
        ]
        if self.compute_environment.cmd:
            command = json.loads(self.compute_environment.cmd) + command
        job = {
            "name": f"Engage-Model-Run-UserId-{user_id}-RunId-{run_id}",
            "command": command,
            "definition": self.get_job_definition()
        }
        return job

    def describe_jobs(self, jobs: list) -> list:
        if not jobs:
            return [], True
        
        all_compelete = True
        uncomplete_status = ["SUBMITTED", "PENDING", "RUNNABLE", "STARTING", "RUNNING"]

        response = self.client.describe_jobs(jobs=jobs)
        result = {}
        for item in response["jobs"]:
            result[item["jobId"]] =  item["status"]
            if  item["status"] in uncomplete_status:
                all_compelete = False
        return result, all_compelete

    def terminate_job(self, job_id):
        response = self.client.terminate_job(
            jobId=job_id,
            reason="Job terminated manually by Engage user."
        )
        return response
