"""
User Celery signals to update celery task instances.
"""
import pytz
import time
import traceback as pytraceback
from datetime import datetime
from celery import states, signals
from .models import CeleryTask


def befor_task_publish_handler(sender=None, body=None, headers=None, **kwargs):
    """
    Create CeleryTask instance
    """
    task_id = headers["id"]
    task, _ = CeleryTask.objects.get_or_create(task_id=task_id)
    task.status = states.PENDING
    task.save()


def task_prerun_handler(task_id, task=None, *args, **kwargs):
    """
    Set task status to be STARTED
    """
    # Ensure CeleryTask instance created, and avoid race condition with before_task_publish
    attempts = 0
    while attempts < 20:
        try:
            task = CeleryTask.objects.get(task_id=task_id)
            if task:
                task.status = states.STARTED
                task.date_start = datetime.now(pytz.utc)
                task.save()
            break
        except CeleryTask.DoesNotExist:
            attempts += 1
            time.sleep(0.5)


def task_success_handler(sender, result=None, **kwargs):
    """
    Set task status to be SUCCESS.
    """
    task = CeleryTask.objects.get(task_id=sender.request.id)
    task.status = states.SUCCESS
    task.date_done = datetime.utcnow()
    task.result = result
    task.save()


def task_failure_handler(task_id, exception=None, traceback=None, einfo=None, *args, **kwargs):
    """
    Set task status to be FAILURE
    """
    task = CeleryTask.objects.get(task_id=task_id)
    task.status = states.FAILURE
    task.traceback = "".join(pytraceback.format_tb(traceback))
    task.date_done = datetime.utcnow()
    task.save()


def enable_state_handlers():
    """
    To enable celery task handlers on different task state
    """
    signals.before_task_publish.connect(befor_task_publish_handler)
    signals.task_prerun.connect(task_prerun_handler)
    signals.task_success.connect(task_success_handler)
    signals.task_failure.connect(task_failure_handler)
