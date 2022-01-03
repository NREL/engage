import uuid

from django.conf import settings
from django.test import TestCase
from django.urls import reverse, resolve
from django.utils import translation


class AccountUserURLTestCase(TestCase):
    def test_user_registration(self):
        view_name = "user_registration"

        for language_code, _ in settings.LANGUAGES:
            with translation.override(language_code):
                url = f"/{language_code}/api/user_registration/"
                self.assertEqual(reverse(view_name), url)
                self.assertEqual(resolve(url).view_name, view_name)

    def test_user_activation(self):
        activation_uuid = str(uuid.uuid4())
        view_name = "user_activation"

        for language_code, _ in settings.LANGUAGES:
            with translation.override(language_code):
                url = f"/{language_code}/api/user_activation/{activation_uuid}"
                self.assertEqual(
                    reverse(view_name, kwargs={"activation_uuid": activation_uuid}), url
                )
                self.assertEqual(resolve(url).view_name, view_name)

    def test_password(self):
        view_name = "password"
        for language_code, _ in settings.LANGUAGES:
            with translation.override(language_code):
                url = f"/{language_code}/settings/password/"
                self.assertEqual(reverse(view_name), url)
                self.assertEqual(resolve(url).view_name, view_name)

    def test_login(self):
        view_name = "login"
        for language_code, _ in settings.LANGUAGES:
            with translation.override(language_code):
                url = f"/{language_code}/login/"
                self.assertEqual(reverse(view_name), url)
                self.assertEqual(resolve(url).view_name, view_name)
