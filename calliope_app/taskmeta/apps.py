from django.apps import AppConfig


class TaskmetaConfig(AppConfig):
    name = "taskmeta"

    def ready(self):
        try:
            from .signals import enable_state_handlers
        except ImportError:
            raise
        enable_state_handlers()
