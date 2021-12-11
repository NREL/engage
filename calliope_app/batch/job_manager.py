import json
import logging
import boto3
# from django.conf import settings

logger = logging.getLogger(__name__)


class BatchJobManager:
    
    def submit_job(self, job):
        from types import SimpleNamespace
        settings = SimpleNamespace(
            AWS_REGION_NAME="us-west-2",
            AWS_BATCH_JOB_QUEUE="engage-job-queue",
            AWS_BATCH_TAGS='{"org":"engage","billingId":"210036"}'
        )
        
        client = boto3.client("batch", region_name=settings.AWS_REGION_NAME)
        client.submit_job(
            jobName=job["name"],
            jobQueue=settings.AWS_BATCH_JOB_QUEUE,
            jobDefinition=job["definition"],
            containerOverrides={"command": job["command"]},
            # tags=json.loads(settings.AWS_BATCH_TAGS),
        )
        print("submmitted")
        logger.info("Batch job submitted - %s", job["name"])

    def generate_job_message(self, run_id, user_id):
        job = {
            "name": "engage-test-job",
            "command": [
                "engage", "solve-model",
                "--run-id", str(run_id),
                "--user-id", str(user_id)
            ],
            "definition": "engage-mem2-dev"
        }
        return job


if __name__ == "__main__":
    bm = BatchJobManager()
    job = bm.generate_job_message(run_id=1290, user_id=34)
    bm.submit_job(job)
