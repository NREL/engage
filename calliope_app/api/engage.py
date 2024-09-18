import boto3
from botocore.exceptions import BotoCoreError, ClientError

from django.conf import settings
from django.core.mail.backends.base import BaseEmailBackend
from django.core.mail.message import sanitize_address


ENGAGE_SOLVERS = [
    {
        "name": "appsi_highs",
        "pretty_name": "HiGHS",
        "order": 1,
        "is_active": True
    },
    {
        "name": "cbc",
        "pretty_name": "CBC",
        "order": 2,
        "is_active": True
    },
    {
        "name": "amplxpress",
        "pretty_name": "Xpress",
        "order": 3,
        "is_active": False
    }
]


def aws_ses_configured():
    """
    Check the configuration of AWS SES settings

    :return: bool, True if well configured, False if not.
    """
    cond1 = True if settings.AWS_SES_REGION_NAME else False
    cond2 = True if settings.AWS_SES_REGION_ENDPOINT else False
    cond3 = True if settings.AWS_SES_FROM_EMAIL else False

    return cond1 and cond2 and cond3


class EmailBackend(BaseEmailBackend):

    def __init__(self, fail_silently=False, **kwargs):
        """Init SES client using boto3"""
        super().__init__(fail_silently=fail_silently)

        # AWS settings
        aws_access_key_id = getattr(settings, 'AWS_ACCESS_KEY_ID', None)
        aws_secret_access_key = getattr(settings, 'AWS_SECRET_ACCESS_KEY', None)
        aws_ses_region_name = getattr(settings, 'AWS_SES_REGION_NAME')

        self.client = boto3.client(
            service_name='ses',
            aws_access_key_id=aws_access_key_id,
            aws_secret_access_key=aws_secret_access_key,
            region_name=aws_ses_region_name
        )

    def send_messages(self, email_messages):
        """Send messages"""
        if not email_messages:
            return

        sent_message_count = 0

        for email_message in email_messages:
            if self._send(email_message):
                sent_message_count += 1

        return sent_message_count

    def _send(self, email_message):
        """Send message"""
        recipients = email_message.recipients()
        if not recipients:
            return False

        encoding = email_message.encoding or settings.DEFAULT_CHARSET
        from_email = sanitize_address(email_message.from_email, encoding)

        recipients = [sanitize_address(addr, encoding) for addr in email_message.recipients()]
        message = email_message.body
        subject = email_message.subject

        try:
            kwargs = {
                'Source': from_email,
                'Destination': {
                    'ToAddresses': recipients
                },
                'Message': {
                    'Body': {
                        'Text': {
                            'Charset': 'UTF-8',
                            'Data': message
                        }
                    },
                    'Subject': {
                        'Charset': 'UTF-8',
                        'Data': subject
                    }
                }
            }
            self.client.send_email(**kwargs)
        except (BotoCoreError, ClientError) as e:
            print(e)
            if not self.fail_silently:
                raise
            return False

        return True
