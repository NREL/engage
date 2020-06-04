import os
from django.apps import AppConfig
from django.conf import settings


class ApiConfig(AppConfig):
    name = 'api'

    def ready(self):
        if not os.path.exists(settings.DATA_STORAGE):
            os.makedirs(settings.DATA_STORAGE, exist_ok=True)
