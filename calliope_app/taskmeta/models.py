from django.db import models
from django.contrib.postgres import fields
from celery import states

CELERY_TASK_STATE_CHOICES = sorted(zip(states.ALL_STATES, states.ALL_STATES))

class BatchTaskStatus:
    SUBMITTED = "SUBMITTED"
    PENDING = "PENDING"
    RUNNABLE = "RUNNABLE"
    STARTING = "STARTEDING"
    RUNNING = "RUNNING"
    SUCCEEDED = "SUCCEEDED"
    FAILED = "FAILED"

batch_task_status = BatchTaskStatus

BATCH_TASK_STATE_CHOICES = (
    (batch_task_status.SUBMITTED, batch_task_status.SUBMITTED),
    (batch_task_status.PENDING, batch_task_status.PENDING),
    (batch_task_status.RUNNABLE, batch_task_status.RUNNABLE),
    (batch_task_status.STARTING, batch_task_status.STARTING),
    (batch_task_status.RUNNING, batch_task_status.RUNNING),
    (batch_task_status.SUCCEEDED, batch_task_status.SUCCEEDED),
    (batch_task_status.FAILED, batch_task_status.FAILED)
)


class CeleryTask(models.Model):
    """
    Celery Task Class
    """
    task_id = models.CharField(max_length=36, null=True, editable=False)
    status = models.CharField(max_length=50, default=states.PENDING, choices=CELERY_TASK_STATE_CHOICES)
    date_start = models.DateTimeField(null=True, editable=False)
    date_done = models.DateTimeField(null=True, editable=False)
    result = fields.JSONField(null=True, default=None)
    traceback = models.TextField(null=True, default=None)
    
    class Meta:
        db_table = "celery_task"
        verbose_name_plural = "[Admin] Celery Tasks"

    def __str__(self):
        return "<Celery Task: {0.task_id} state={0.status}>".format(self)


class BatchTask(models.Model):
    """
    Batch Task Class
    """
    task_id = models.CharField(max_length=36, null=True, editable=False)
    status = models.CharField(max_length=20, default=None, choices=BATCH_TASK_STATE_CHOICES)
    date_start = models.DateTimeField(null=True, editable=False)
    date_done = models.DateTimeField(null=True, editable=False)
    traceback = models.TextField(null=True, default=None)
    
    class Meta:
        db_table = "batch_task"
        verbose_name_plural = "[Admin] Batch Task"
    
    def __str__(self):
        return "<Batch Task: {0.task_id} state={0.status}>".format(self)
