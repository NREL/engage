from django.db import models
from django.contrib.postgres import fields
from celery import states

CELERY_TASK_STATE_CHOICES = sorted(zip(states.ALL_STATES, states.ALL_STATES))


class CeleryTask(models.Model):
    """
    Celery Task Class
    """
    class Meta:
        db_table = "celery_task"
        verbose_name_plural = "[Admin] Celery Tasks"

    task_id = models.CharField(max_length=36, null=True, editable=False)
    status = models.CharField(max_length=50, default=states.PENDING, choices=CELERY_TASK_STATE_CHOICES)
    date_start = models.DateTimeField(null=True, editable=False)
    date_done = models.DateTimeField(null=True, editable=False)
    result = models.JSONField(null=True, default=None)
    traceback = models.TextField(null=True, default=None)

    def __str__(self):
        return "<Task: {0.task_id} state={0.status}>".format(self)
