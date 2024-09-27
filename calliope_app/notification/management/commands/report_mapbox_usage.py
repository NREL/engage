from django.core.management.base import BaseCommand
from notification.tasks import send_mapbox_usage_email


class Command(BaseCommand):
    help = 'Query Mapbox usage and send email'

    def handle(self, *args, **kwargs):
        """Report Mapbox usage information"""
        send_mapbox_usage_email()
