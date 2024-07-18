import logging
from datetime import datetime

from django.core.mail import EmailMultiAlternatives
from django.conf import settings
from django.contrib.auth.models import User

from api.models.engage import RequestRateLimit

logger = logging.getLogger(__name__)


def send_mapbox_usage_email():

    now = datetime.now()
    month = now.strftime('%b')

    try:
        limit = RequestRateLimit.objects.get(
            year=now.year,
            month=now.month,
        )
    except RequestRateLimit.DoesNotExist:
        logger.error('Failed to query mapbox usage - %s, %s !', month, now.year)
        return

    subject=f'Engage Mapbox Usage [{month}, {now.year}]'
    from_email = settings.AWS_SES_FROM_EMAIL
    recipient_list = ["engage@nrel.gov"]
    recipient_list.extend([admin.email for admin in User.objects.filter(is_superuser=True)])

    text_content = f"""
    Hello Engage Admin,

    This is a weekly update email about Mapbox usage of current month!
    Mapbox loads used till today in {month} {now.year} is "{limit.total}/50,000"

    Map loads exceed 50,000 will be charged, please check Mapbox pricing for more information.

    --Engage System
    """

    msg = EmailMultiAlternatives(
        subject=subject,
        body=text_content,
        from_email=from_email,
        to=recipient_list
    )
    msg.send()

    logger.info(
        'Mapbox usage email sent! Used loads %s / 50,0000 in %s, %s !',
        limit.total, month, now.year
    )
