"""
Unit tests for Django app "client" views/engage
"""

from django.contrib.auth.models import User
from django.urls import reverse
from django.test import TestCase

from api.models.configuration import (
    Model,
    Model_User
)


class HomeViewTestCase(TestCase):
    
    def setUp(self):
        self.user = User.objects.create_user(
            username="my-username", email="my-email@example.com", password="my-password"
        )
        self.model = Model.objects.create(name="my-model", public=True)
        self.model_user = Model_User.objects.create(
            user=self.user, model=self.model, can_edit=True,
        )
        self.client.login(username="my-username", password="my-password")
    
    def tearDown(self):
        self.client.logout()
    
    def test_home_view(self):
        response = self.client.get(reverse("home"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.model.name)


class ShareViewTestCase(TestCase):
    
    def setUp(self):
        self.user = User.objects.create_user(
            username="my-username", email="my-email@example.com", password="my-password"
        )
        self.model = Model.objects.create(name="my-model", public=True)
        self.model_user = Model_User.objects.create(
            user=self.user, model=self.model, can_edit=True,
        )
        self.client.login(username="my-username", password="my-password")
    
    def tearDown(self):
        self.client.logout()
    
    def test_share_view(self):
        response = self.client.get(reverse("settings"))
        self.assertEqual(response.status_code, 200)


class PasswordViewTestCase(TestCase):
    
    def setUp(self):
        self.user = User.objects.create_user(
            username="my-username", email="my-email@example.com", password="my-password"
        )
        self.client.login(username="my-username", password="my-password")
    
    def tearDown(self):
        self.client.logout()
    
    def test_password_view(self):
        response = self.client.get(reverse("password"))
        self.assertEqual(response.status_code, 200)


class AdminLoginViewTestCase(TestCase):
    
    def setUp(self):
        self.user = User.objects.create_user(
            username="my-username", email="my-email@example.com", password="my-password"
        )
        self.client.login(username="my-username", password="my-password")
    
    def tearDown(self):
        self.client.logout()
    
    def test_admin_login_view(self):
        response = self.client.get(reverse("password"))
        self.assertEqual(response.status_code, 200)


class UserLoginViewTestCase(TestCase):
    
    def test_user_login__alrerady_login(self):
        user = User.objects.create_user(
            username="my-username", email="my-email@example.com", password="my-password"
        )
        self.client.login(username="my-username", password="my-password")
        response = self.client.get(reverse("login"))
        self.assertEqual(response.status_code, 302)
        self.client.logout()
    
    def test_user_login__public_models_without_login(self):
        model = Model.objects.create(name="public-model", public=True)
        response = self.client.get(reverse("login"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, model.name)
    
    def test_user_login__user_inactive(self):
        user = User.objects.create_user(
            username="my-username", email="my-email@example.com", password="my-password",
            is_active=False
        )
        data = {
            "email": "my-username",
            "password": "my-password"
        }
        response = self.client.post(reverse("login"), data=data)
        self.assertEqual(response.status_code, 302)
        self.assertIn("login/?status=inactive", response.url)
        self.client.logout()

    def test_user_login__invalid_email(self):
        user = User.objects.create_user(
            username="my-username", email="my-email@example.com", password="my-password",
            is_active=False
        )
        data = {
            "email": "my-username2",
            "password": "my-password"
        }
        response = self.client.post(reverse("login"), data=data)
        self.assertEqual(response.status_code, 302)
        self.assertIn("login/?status=invalid-email", response.url)
        self.client.logout()

    def test_user_login__authenticate(self):
        user = User.objects.create_user(
            username="my-username", email="my-email@example.com", password="my-password"
        )
        data = {
            "email": "my-username",
            "password": "my-password"
        }
        response = self.client.post(reverse("login"), data=data)
        self.assertEqual(response.status_code, 302)
        self.client.logout()
