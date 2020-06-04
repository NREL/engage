"""
Unit tests for Django app "client" views/outputs
"""

from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse


from api.models.configuration import (
    Model,
    Model_User,
    Scenario
)
from api.models.outputs import Run


class RunsViewTestCase(TestCase):
    
    def setUp(self):
        self.user = User.objects.create_user(
            username="my-username", email="my-email@example.com", password="my-password"
        )
        self.model = Model.objects.create(name="my-model", public=True)
        self.model_user = Model_User.objects.create(
            user=self.user, model=self.model, can_edit=True,
        )
        self.scenario = Scenario.objects.create(
            name="my-scenario",
            model=self.model
        )
    
    def test_runs_view__public_model(self):
        response = self.client.get(reverse("runs", kwargs={"model_uuid": str(self.model.uuid)}))
        self.assertEqual(response.status_code, 200)

    def test_runs_view__private_model(self):
        self.model.public = False
        self.model.save()
        response = self.client.get(reverse("runs", kwargs={"model_uuid": str(self.model.uuid)}))
        self.assertEqual(response.status_code, 302)


class AddRunsViewTestCase(TestCase):
    
    def setUp(self):
        self.user = User.objects.create_user(
            username="my-username", email="my-email@example.com", password="my-password"
        )
        self.model = Model.objects.create(name="my-model", public=True)
        self.model_user = Model_User.objects.create(
            user=self.user, model=self.model, can_edit=True,
        )
        self.scenario = Scenario.objects.create(
            name="my-scenario",
            model=self.model
        )
        self.client.login(username="my-username", password="my-password")
    
    def tearDown(self):
        self.client.logout()
    
    def test_add_runs_view(self):
        response = self.client.get(reverse("add_runs", kwargs={
            "model_uuid": str(self.model.uuid),
            "scenario_id": self.scenario.id
        }))
        self.assertEqual(response.status_code, 200)


class MapVizViewTestCase(TestCase):
    
    def setUp(self):
        self.user = User.objects.create_user(
            username="my-username", email="my-email@example.com", password="my-password"
        )
        self.model = Model.objects.create(name="my-model", public=True)
        self.model_user = Model_User.objects.create(
            user=self.user, model=self.model, can_edit=True,
        )
        self.scenario = Scenario.objects.create(
            name="my-scenario", model=self.model, description="my-scenario-description"
        )
        self.model_run = Run.objects.create(
            scenario=self.scenario,
            subset_time="2015-01-01 to 2015-01-02",
            year=2015,
            status="QUEUED",
            message="run message",
            inputs_path="/this/is/inputs",
            logs_path="/this/is/logs.html",
            outputs_path="/this/is/outputs",
            plots_path="/this/is/plots.html",
            model=self.model,
            description="my-run-description",
        )
    
    def test_map_viz_view(self):
        response = self.client.get(reverse("map_viz", kwargs={
            "model_uuid": str(self.model.uuid),
            "run_id": self.model_run.id
        }))
        self.assertEqual(response.status_code, 200)
