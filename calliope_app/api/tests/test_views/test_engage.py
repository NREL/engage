"""
Unit tests for Django app "api" views/engage
"""
import json

from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from api.models.engage import User_Profile


class UserActivationViewTestCase(TestCase):
    
    def setUp(self):
        self.user = User.objects.create_user(
            username="my-username",
            email="my-email@example.com",
            password="my-password"
        )
        self.user_profile = User_Profile.objects.create(
            user=self.user,
            organization="my-organization"
        )
    
    def test_user_activation(self):
        response = self.client.get(reverse(
            "user_activation", 
            kwargs={"activation_uuid": self.user_profile.activation_uuid}
        ))
        self.assertEqual(response.status_code, 302)


class UserRegistrationViewTestCase(TestCase):
    
    def test_register(self):
        data = {
            "first_name": "my-firstname",
            "last_name": "my-lastname",
            "organization": "my-organization",
            "email": "my-new-email@example.com",
            "password": "my-new-password"
        }
        response = self.client.post(
            reverse("register"), 
            data=data, 
            HTTP_HOST="localhost"
        )
        self.assertEqual(response.status_code, 200)
        
        user = User.objects.get(email="my-new-email@example.com")
        self.assertContains(response, user.email)
