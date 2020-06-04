"""
Unit tests for Django app "client" views/configuration.
"""

import uuid

from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from api.models.configuration import (
    Model,
    Model_User,
    Location,
    Abstract_Tech,
    Technology,
    Loc_Tech,
    Scenario,
    User_File,
    Timeseries_Meta,
    Parameter
)


class ModelViewTestCase(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="my-username", email="my-email@example.com", password="my-password"
        )
        self.model = Model.objects.create(name="my-model")
        self.model_user = Model_User.objects.create(user=self.user, model=self.model)
        self.public_model = Model.objects.create(name="public-model", public=True)
        self.client.login(username="my-username", password="my-password")

    def tearDown(self):
        self.client.logout()

    def test_model_view__not_existing_model(self):
        response = self.client.get(
            reverse("model", kwargs={"model_uuid": str(uuid.uuid4())})
        )
        self.assertEqual(response.status_code, 302)

    def test_model_view__public_model(self):
        response = self.client.get(
            reverse("model", kwargs={"model_uuid": str(self.public_model.uuid)})
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.public_model.name)

    def test_model_view__can_edit(self):
        response = self.client.get(
            reverse("model", kwargs={"model_uuid": str(self.model.uuid)})
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.model.name)


class LocationsViewTestCase(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="my-username", email="my-email@example.com", password="my-password"
        )
        self.model = Model.objects.create(name="my-model")
        self.model_user = Model_User.objects.create(
            user=self.user, model=self.model, can_edit=True,
        )
        self.client.login(username="my-username", password="my-password")

    def tearDown(self):
        self.client.logout()

    def test_locations_view__no_location(self):
        response = self.client.get(
            reverse("locations", kwargs={"model_uuid": str(self.model.uuid)})
        )
        self.assertEqual(response.status_code, 200)

    def test_locations_view__with_location(self):
        location1 = Location.objects.create(
            name="my-location-one",
            pretty_name="MyLocationOne",
            latitude=40.1,
            longitude=-108.2,
            model=self.model,
        )
        location2 = Location.objects.create(
            name="my-location-two",
            pretty_name="MyLocationTwo",
            latitude=41.5,
            longitude=-107.1,
            model=self.model,
        )
        response = self.client.get(
            reverse("locations", kwargs={"model_uuid": str(self.model.uuid)})
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, location1.pretty_name)
        self.assertContains(response, location2.pretty_name)


class TechnologiesViewTestCase(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="my-username", email="my-email@example.com", password="my-password"
        )
        self.model = Model.objects.create(name="my-model")
        self.model_user = Model_User.objects.create(
            user=self.user, model=self.model, can_edit=True,
        )
        self.client.login(username="my-username", password="my-password")

    def tearDown(self):
        self.client.logout()

    def test_technologies_view__no_technology(self):
        response = self.client.get(
            reverse("technologies", kwargs={"model_uuid": str(self.model.uuid)})
        )
        self.assertEqual(response.status_code, 200)

    def test_technologies_view__with_technology(self):
        abstract_tech = Abstract_Tech.objects.create(
            name="my-abstract-tech",
            pretty_name="MyAbstractTech",
            image="my-abstract-tech.png",
        )
        tech = Technology.objects.create(
            abstract_tech=abstract_tech,
            name="my-technology",
            pretty_name="MyTechnology",
            model=self.model,
        )
        response = self.client.get(
            reverse("technologies", kwargs={"model_uuid": str(self.model.uuid)}),
            data={"tech_id": tech.id},
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, tech.pretty_name)


class AddTechnologiesViewTestCase(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="my-username", email="my-email@example.com", password="my-password"
        )
        self.client.login(username="my-username", password="my-password")

    def tearDown(self):
        self.client.logout()

    def test_add_technologies_view__private_model(self):
        model = Model.objects.create(name="my-model")
        model_user = Model_User.objects.create(
            user=self.user, model=model, can_edit=True,
        )
        abstract_tech = Abstract_Tech.objects.create(
            name="my-abstract-tech",
            pretty_name="MyAbstractTech",
            image="my-abstract-tech.png",
        )
        tech = Technology.objects.create(
            abstract_tech=abstract_tech,
            name="my-technology",
            pretty_name="MyTechnology",
            model=model,
        )
        response = self.client.get(
            reverse("technologies", kwargs={"model_uuid": str(model.uuid)})
        )
        self.assertEqual(response.status_code, 200)

    def test_add_technologies_view__public_model(self):
        public_model = Model.objects.create(name="public-model", public=True)
        model_user = Model_User.objects.create(
            user=self.user, model=public_model, can_edit=True,
        )
        abstract_tech = Abstract_Tech.objects.create(
            name="my-abstract-tech",
            pretty_name="MyAbstractTech",
            image="my-abstract-tech.png",
        )
        tech = Technology.objects.create(
            abstract_tech=abstract_tech,
            name="my-public-technology",
            pretty_name="MyPublicTechnology",
            model=public_model,
        )
        response = self.client.get(
            reverse("technologies", kwargs={"model_uuid": str(public_model.uuid)})
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, tech.pretty_name)


class LocTechsViewTestCase(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="my-username", email="my-email@example.com", password="my-password"
        )
        self.model = Model.objects.create(name="my-model")
        self.model_user = Model_User.objects.create(
            user=self.user, model=self.model, can_edit=True,
        )
        self.abstract_tech = Abstract_Tech.objects.create(
            name="my-abstract-tech",
            pretty_name="MyAbstractTech",
            image="my-abstract-tech.png",
        )
        self.tech = Technology.objects.create(
            abstract_tech=self.abstract_tech,
            name="my-public-technology",
            pretty_name="MyPublicTechnology",
            model=self.model,
        )
        self.location1 = Location.objects.create(
            name="my-location-one",
            pretty_name="MyLocationOne",
            latitude=40.1,
            longitude=-108.2,
            model=self.model,
        )
        self.location2 = Location.objects.create(
            name="my-location-two",
            pretty_name="MyLocationTwo",
            latitude=41.5,
            longitude=-107.1,
            model=self.model,
        )
        self.loc_tech = Loc_Tech.objects.create(
            location_1=self.location1,
            location_2=self.location2,
            technology=self.tech,
            model=self.model,
        )
        self.client.login(username="my-username", password="my-password")

    def tearDown(self):
        self.client.logout()

    def test_loc_techs_view(self):
        data = {"tech_id": self.tech.id, "loc_tech_id": self.loc_tech.id}
        response = self.client.get(
            reverse("loc_techs", kwargs={"model_uuid": str(self.model.uuid)})
        )
        self.assertEqual(response.status_code, 200)


class ScenariosViewTestCase(TestCase):
    
    def setUp(self):
        self.user = User.objects.create_user(
            username="my-username", email="my-email@example.com", password="my-password"
        )
        self.model = Model.objects.create(name="my-model")
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

    def test_scenarios_view(self):
        response = self.client.get(
            reverse("scenarios", kwargs={"model_uuid": str(self.model.uuid)})
        )
        self.assertEqual(response.status_code, 200)


class AddScenariosViewTestCase(TestCase):
    
    def setUp(self):
        self.user = User.objects.create_user(
            username="my-username", email="my-email@example.com", password="my-password"
        )
        self.model = Model.objects.create(name="my-model")
        self.model_user = Model_User.objects.create(
            user=self.user, model=self.model, can_edit=True,
        )
        self.scenario = Scenario.objects.create(
            name="my-scenario",
            model=self.model
        )
    
    def test_add_scenarios__before_login(self):
        response = self.client.get(
            reverse("add_scenarios", kwargs={"model_uuid": str(self.model.uuid)})
        )
        self.assertEqual(response.status_code, 302)
        self.assertIn("login/?next", response.url)

    def test_add_scenarios__after_login(self):
        self.client.login(username="my-username", password="my-password")
        response = self.client.get(
            reverse("add_scenarios", kwargs={"model_uuid": str(self.model.uuid)})
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.scenario.name)
        self.client.logout()


class TimeseriesViewTestCase(TestCase):
    
    def setUp(self):
        self.user = User.objects.create_user(
            username="my-username", email="my-email@example.com", password="my-password"
        )
        self.model = Model.objects.create(name="my-model")
        self.model_user = Model_User.objects.create(
            user=self.user, model=self.model, can_edit=True,
        )
        self.user_file = User_File.objects.create(
            filename="user_files/my-test.csv",
            model=self.model
        )
    
    def test_timeseries_view__before_login(self):
        response = self.client.get(
            reverse("timeseries", kwargs={"model_uuid": str(self.model.uuid)})
        )
        self.assertEqual(response.status_code, 302)
        self.assertIn("login/?next", response.url)

    def test_timeseries_view__after_login(self):
        self.client.login(username="my-username", password="my-password")
        response = self.client.get(
            reverse("timeseries", kwargs={"model_uuid": str(self.model.uuid)})
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, str(self.user_file.filename).split("/")[-1])
        self.client.logout()


class TimeseriesTableViewTestCase(TestCase):

    def setUp(self):
        self.user = User.objects.create_user(
            username="my-username", email="my-email@example.com", password="my-password"
        )
        self.model = Model.objects.create(name="my-model")
        self.model_user = Model_User.objects.create(
            user=self.user, model=self.model, can_edit=True,
        )
        self.timeseries_meta = Timeseries_Meta.objects.create(
            name="my-timeseries-meta",
            model=self.model
        )
    
    def test_timeseries_table__before_login(self):
        response = self.client.get(
            reverse("timeseries_table", kwargs={"model_uuid": str(self.model.uuid)})
        )
        self.assertEqual(response.status_code, 302)
        self.assertIn("login/?next", response.url)
    
    def test_timeseries_table__after_login(self):
        self.client.login(username="my-username", password="my-password")
        response = self.client.get(
            reverse("timeseries_table", kwargs={"model_uuid": str(self.model.uuid)})
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.timeseries_meta.name)
        self.client.logout()


class ParametersViewTestCase(TestCase):
    
    def setUp(self):
        self.user = User.objects.create_user(
            username="my-username", email="my-email@example.com", password="my-password"
        )
        self.model = Model.objects.create(name="my-model")
        self.model_user = Model_User.objects.create(
            user=self.user, model=self.model, can_edit=True,
        )
        self.param = Parameter.objects.create(
            root="root",
            category="public",
            name="my-param-one",
            pretty_name="MyParamOne",
            timeseries_enabled=True,
            choices=["c1", "c2"],
            units="kWh"
        )
    
    def test_parameters_view__before_login(self):
        response = self.client.get(
            reverse("parameters", kwargs={
                "model_uuid": str(self.model.uuid),
                "parameter_name": "resource"
            })
        )
        self.assertEqual(response.status_code, 302)
        self.assertIn("login/?next", response.url)
    
    def test_parameters_view__after_login(self):
        self.client.login(username="my-username", password="my-password")
        response = self.client.get(reverse("parameters", kwargs={
            "model_uuid": str(self.model.uuid),
            "parameter_name": "resource"
        }))
        self.assertEqual(response.status_code, 200)
        self.client.logout()
