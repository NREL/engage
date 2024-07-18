import os
from django.apps import AppConfig
from django.conf import settings


class NotificationConfig(AppConfig):
    name = "notification"

    def ready(self):
        if not os.path.exists(settings.DATA_STORAGE):
            os.makedirs(settings.DATA_STORAGE, exist_ok=True)
