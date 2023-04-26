import os
from django.apps import AppConfig
from django.conf import settings


class GeophiresConfig(AppConfig):
    name = "geophires"

    def ready(self):
        geophires_storage = os.path.join(settings.DATA_STORAGE, "geophires")
        if not os.path.exists(geophires_storage):
            os.makedirs(geophires_storage, exist_ok=True)
