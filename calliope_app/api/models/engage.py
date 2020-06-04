from django.db import models
from django.utils.html import mark_safe
from django.contrib.auth.models import User
from django.urls import reverse
from django.template.loader import render_to_string
from django.core.mail import send_mail
from django.conf import settings

import uuid


class Help_Guide(models.Model):
    class Meta:
        db_table = "help_guide"
        verbose_name_plural = "[Admin] Help Guide"

    key = models.CharField(max_length=200)
    html = models.TextField(blank=True, null=True)

    def __str__(self):
        return '%s' % (self.key)

    def safe_html(self):
        """ Allows stored html to be rendered in HTML """
        return mark_safe(self.html)

    @classmethod
    def get_safe_html(cls, key):
        """ Retrieve the html content based on key """
        record = cls.objects.filter(key=key).first()
        if record:
            return mark_safe(record.html)
        else:
            return 'Not Available'


class User_Profile(models.Model):
    class Meta:
        db_table = "user_profile"
        verbose_name_plural = "[0] User Profiles"

    user = models.OneToOneField(User, on_delete=models.CASCADE)
    organization = models.TextField(blank=True, null=True)
    timezone = models.TextField(default="UTC")
    activation_uuid = models.UUIDField(default=uuid.uuid4)

    def __str__(self):
        return '%s %s' % (self.user.first_name, self.user.last_name)

    @staticmethod
    def register(http_host, email, password,
                 first_name, last_name, organization):
        """ Register a new user w/ email verification """

        user = User.objects.filter(email=email).first()
        if not user:
            user = User.objects.create_user(username=email,
                                            email=email,
                                            first_name=first_name,
                                            last_name=last_name,
                                            password=password,
                                            is_active=False)
            user.save()
            profile = User_Profile.objects.create(user=user,
                                                  organization=organization)
        else:
            profile = User_Profile.objects.filter(user=user).first()
            if profile is None:
                profile = User_Profile.objects.create(
                    user=user, organization=organization)

        # Email user the activation link
        url_kwargs = {'activation_uuid': profile.activation_uuid}
        relative_url = reverse('user_activation', kwargs=url_kwargs)
        activation_url = http_host + relative_url
        context = {
            "first_name": first_name,
            "activation_url": activation_url,
        }
        message = render_to_string("registration/user_activation.txt", context)
        send_mail(
            subject="NREL ENGAGE Registration",
            message=message,
            from_email=settings.AWS_SES_FROM_EMAIL,
            recipient_list=[email]
        )

        return profile

    @classmethod
    def activate(cls, activation_uuid):
        """ Activate a new user based on their unique activation_uuid """
        profile = cls.objects.filter(activation_uuid=activation_uuid)
        user = profile.first().user
        user.is_active = True
        user.save()
        return True
