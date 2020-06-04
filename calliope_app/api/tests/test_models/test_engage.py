"""
Unit tests for Django app 'api' models - api/models/configuration.
"""
from mock import patch

from django.contrib.auth.models import User
from django.test import TestCase
from django.utils.html import mark_safe
from django.utils.safestring import SafeString

from api.models.engage import Help_Guide, User_Profile


class HelpGuideTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.help_guide = Help_Guide.objects.create(
            key="my-key", html="<p>This is Help Guide.</>"
        )

    def test_class_meta(self):
        self.assertEqual(Help_Guide._meta.db_table, "help_guide")
        self.assertEqual(Help_Guide._meta.verbose_name_plural, "[Admin] Help Guide")

    def test_string_representation(self):
        self.assertEqual(str(self.help_guide), self.help_guide.key)

    def test_safe_html(self):
        self.assertIsInstance(self.help_guide.safe_html(), SafeString)

    def test_get_safe_html__available(self):
        result = Help_Guide.get_safe_html(key="my-key")
        self.assertEqual(result, mark_safe(self.help_guide.html))

    def test_get_safe_html__not_available(self):
        result = Help_Guide.get_safe_html(key="unknown-key")
        self.assertEqual(result, "Not Available")


class UserProfileTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create_user(
            username="user1", password="user1-password", email="user1-email@example.com"
        )
        cls.user_profile = User_Profile.objects.create(
            user=cls.user, organization="my-organizaiton1"
        )

    def test_class_meta(self):
        self.assertEqual(User_Profile._meta.db_table, "user_profile")
        self.assertEqual(User_Profile._meta.verbose_name_plural, "[0] User Profiles")

    def test_string_representation(self):
        self.assertEqual(
            str(self.user_profile), f"{self.user.first_name} {self.user.last_name}"
        )

    @patch("api.models.engage.send_mail")
    def test_register__user_not_existing(self, send_mail):
        result_profile = User_Profile.register(
            http_host="localhost",
            email="my-email@example.com",
            password="my-password",
            first_name="my-firstname",
            last_name="my-lastname",
            organization="my-organization2",
        )
        self.assertTrue(send_mail.called)
        self.assertEqual(result_profile.user.email, "my-email@example.com")

    @patch("api.models.engage.send_mail")
    def test_register__user_existing(self, send_mail):
        user = User.objects.create_user(
            username="user2", password="user2-password", email="user2-email@example.com"
        )
        result_profile = User_Profile.register(
            http_host="localhost",
            email="user2-email@example.com",
            password="my-password",
            first_name="my-firstname",
            last_name="my-lastname",
            organization="my-organization3",
        )
        self.assertTrue(send_mail.called)
        self.assertEqual(result_profile.user.email, "user2-email@example.com")
