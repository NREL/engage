from __future__ import absolute_import, unicode_literals

import os
from kombu import Queue
from celery import Celery


# Set the default Django settings momdule for the 'celery' program
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "calliope_app.settings.local")

# Celery App
app = Celery("calliope_app")
app.config_from_object("django.conf:settings", namespace="CELERY")
app.conf.tasks_queues = (
    Queue(name='short_queue', exchange='short_exchange', routing_key='short_key'),
    Queue(name='long_queue', exchange='long_exchange', routing_key='long_key')
)
app.autodiscover_tasks()


@app.task(bind=True)
def debug_task(self):
    print("Request: {0!r}".format(self.request))
