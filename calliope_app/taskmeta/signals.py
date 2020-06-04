"""
User Celery signals to update celery task instances.
"""
import traceback as pytraceback
from datetime import datetime
from celery import states, signals
from .models import CeleryTask


def task_received_handler(request, args, kwargs, **extras):
    """
    Set task status to be RECEIVED.
    """
    task_id = request.task_id
    task, _ = CeleryTask.objects.get_or_create(task_id=task_id)
    task.status = states.RECEIVED
    task.save()


def task_prerun_handler(task_id, task, args, kwargs, **extras):
    """
    Set task status to be STARTED
    """
    task, _ = CeleryTask.objects.get_or_create(task_id=task_id)
    task.status = states.STARTED
    task.date_start = datetime.utcnow()
    task.save()


def task_success_handler(sender, result, **extras):
    """
    Set task status to be SUCCESS.
    """
    task, _ = CeleryTask.objects.get_or_create(task_id=sender.request.id)
    task.status = states.SUCCESS
    task.date_done = datetime.utcnow()
    task.result = result
    task.save()


def task_failure_handler(task_id, exception, args, kwargs, traceback, einfo, **extras):
    """
    Set task status to be FAILURE
    """
    task, _ = CeleryTask.objects.get_or_create(task_id=task_id)
    task.status = states.FAILURE
    task.traceback = "".join(pytraceback.format_tb(traceback))
    task.date_done = datetime.utcnow()
    task.save()


def enable_state_handlers():
    """
    To enable celery task handlers on different task state
    """
    signals.task_received.connect(task_received_handler)
    signals.task_prerun.connect(task_prerun_handler)
    signals.task_success.connect(task_success_handler)
    signals.task_failure.connect(task_failure_handler)
