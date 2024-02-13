"""
Unit tests for Django app "api" views.
"""
import json
import uuid

from mock import patch, MagicMock
from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from django.urls import reverse

from api.models.calliope import Parameter
from api.models.configuration import (
    Model,
    Model_Comment,
    Model_Favorite,
    Model_User,
    Location,
    Loc_Tech,
    Loc_Tech_Param,
    Abstract_Tech,
    Technology,
    Tech_Param,
    Timeseries_Meta,
    Scenario,
    Scenario_Param,
    Scenario_Loc_Tech,
    Run_Parameter,
    User_File
)


class AddModelViewTestCase(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="my-username", email="my-email@example.com", password="my-password"
        )
        self.template_model = Model.objects.create(name="my-template-model")
        self.client.login(username="my-username", password="my-password")

    def tearDown(self):
        self.client.logout()

    def test_add_model__model_existing(self):
        data = {
            "model_name": "my-template-model",
            "template_model_uuid": self.template_model.uuid,
        }
        response = self.client.post(reverse("add_model"), data=data)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            json.loads(response.content),
            {"message": "A model with that name already exists."},
        )

    def test_add_model__not_existing(self):
        data = {"model_name": "my-model1", "template_model_uuid": str(uuid.uuid4())}
        response = self.client.post(reverse("add_model"), data=data)
        self.assertEqual(response.status_code, 200)

        model = Model.objects.get(name="my-model1")
        self.assertEqual(
            json.loads(response.content),
            {"message": "Added model.", "model_uuid": str(model.uuid)},
        )

        model_user = Model_User.objects.get(model=model, user=self.user)
        self.assertEqual(model_user.can_edit, True)

        model_comment = Model_Comment.objects.get(model=model)
        self.assertEqual(
            model_comment.comment, f"{self.user.get_full_name()} initiated this model."
        )


class RemoveModelViewTestCase(TestCase): 
    def setUp(self):
        self.user = User.objects.create_user(
            username="my-username", email="my-email@example.com", password="my-password"
        )
        self.model = Model.objects.create(name="my-model")
        self.client.login(username="my-username", password="my-password")

    def tearDown(self):
        self.client.logout()

    def test_remove_model(self):
        Model_User.objects.create(model=self.model, user=self.user)
        data = {"model_uuid": str(self.model.uuid)}
        response = self.client.post(reverse("remove_model"), data=data)
        self.assertEqual(response.status_code, 200)


class DuplicateModelViewTestCase(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="my-username", email="my-email@example.com", password="my-password"
        )
        self.model = Model.objects.create(name="my-model")
        self.client.login(username="my-username", password="my-password")

    def tearDown(self):
        self.client.logout()

    def test_duplicate_model(self):
        Model_User.objects.create(
            model=self.model, user=self.user, can_edit=True,
        )

        # 1st duplicate
        data = {"model_uuid": str(self.model.uuid)}
        response = self.client.post(reverse("duplicate_model"), data=data)
        self.assertEqual(response.status_code, 200)

        model1 = Model.objects.get(snapshot_version=1)
        self.assertEqual(
            json.loads(response.content),
            {
                "message": "duplicated model",
                "old_model_uuid": str(self.model.uuid),
                "new_model_uuid": str(model1.uuid),
            },
        )

        # 2nd duplicate
        data = {"model_uuid": str(self.model.uuid)}
        response = self.client.post(reverse("duplicate_model"), data=data)
        self.assertEqual(response.status_code, 200)

        model2 = Model.objects.get(snapshot_version=2)
        self.assertEqual(
            json.loads(response.content),
            {
                "message": "duplicated model",
                "old_model_uuid": str(self.model.uuid),
                "new_model_uuid": str(model2.uuid),
            },
        )


class AddCollaboratorViewTestCase(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="my-username", email="my-email@example.com", password="my-password"
        )
        self.collaborator = User.objects.create_user(
            username="my-collaborator",
            email="my-collaborator@example.com",
            password="collaborator-password",
        )
        self.model = Model.objects.create(name="my-model")
        self.model_user = Model_User.objects.create(
            user=self.user, model=self.model, can_edit=True
        )
        self.client.login(username="my-username", password="my-password")

    def tearDown(self):
        self.client.logout()

    def test_add_collaborator__unknown_user(self):
        data = {
            "model_uuid": str(self.model.uuid),
            "collaborator_id": "unknown id",
            "collaborator_can_edit": True,
        }
        response = self.client.post(reverse("add_collaborator"), data=data)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            json.loads(response.content),
            {"message": "No user registered by that email."},
        )

    def test_add_collaborator__registered_user(self):
        data = {
            "model_uuid": str(self.model.uuid),
            "collaborator_id": self.collaborator.id,
            "collaborator_can_edit": 1,
        }
        response = self.client.post(reverse("add_collaborator"), data=data)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            json.loads(response.content), {"message": "Added collaborator."}
        )


class AddModelCommentViewTestCase(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="my-username", email="my-email@example.com", password="my-password"
        )
        self.model = Model.objects.create(name="my-model")
        self.client.login(username="my-username", password="my-password")

    def tearDown(self):
        self.client.logout()

    def test_add_model_comment(self):
        Model_User.objects.create(model=self.model, user=self.user, can_edit=True)

        # Add comment - empty string
        data = {"model_uuid": str(self.model.uuid), "comment": ""}
        response = self.client.post(reverse("add_model_comment"), data=data)
        self.assertEqual(
            json.loads(response.content), {"message": "No comment to be added."}
        )

        # Add comment - non-empty string
        data = {"model_uuid": str(self.model.uuid), "comment": "Hello, Commnt"}
        response = self.client.post(reverse("add_model_comment"), data=data)
        self.assertEqual(json.loads(response.content), {"message": "Added comment."})


class UpdateLocationViewTestCase(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="my-username", email="my-email@example.com", password="my-password"
        )
        self.model = Model.objects.create(name="my-model")
        self.model_user = Model_User.objects.create(
            model=self.model, user=self.user, can_edit=True
        )
        self.location = Location.objects.create(
            name="my-location",
            pretty_name="MyLocation",
            latitude=40.1,
            longitude=-108.2,
            model=self.model,
        )
        self.client.login(username="my-username", password="my-password")

    def tearDown(self):
        self.client.logout()

    def test_add_location__model_existing__with_access(self):
        data = {
            "model_uuid": str(self.model.uuid),
            "location_name": "my-location2",
            "location_lat": 29.11,
            "location_long": -106.99,
            "location_area": 2,
            "location_description": "location description",
        }
        response = self.client.post(reverse("update_location"), data=data)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(json.loads(response.content)["message"], "added location")

    def test_update_location__location_not_existing(self):
        data = {
            "model_uuid": str(self.model.uuid),
            "location_id": 100, 
            "location_name": "my-location2",
            "location_lat": 29.11,
            "location_long": -106.99,
            "location_area": 2,
            "location_description": "location description",
        }
        response = self.client.post(reverse("update_location"), data=data)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(json.loads(response.content)["message"], "edited location")

    def test_update_location__model_existing__with_access(self):
        data = {
            "model_uuid": str(self.model.uuid),
            "location_id": self.location.id,
            "location_name": "my-location",
            "location_lat": 39.11,
            "location_long": 106.99,
            "location_area": -7,
            "location_description": "location description",
        }
        response = self.client.post(reverse("update_location"), data=data)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(json.loads(response.content)["message"], "edited location")


class DeleteLocationViewTestCase(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="my-username", email="my-email@example.com", password="my-password"
        )
        self.model = Model.objects.create(name="my-model")
        self.model_user = Model_User.objects.create(
            model=self.model, user=self.user, can_edit=True
        )
        self.location = Location.objects.create(
            name="my-location",
            pretty_name="MyLocation",
            latitude=40.1,
            longitude=-108.2,
            model=self.model,
        )
        self.client.login(username="my-username", password="my-password")

    def tearDown(self):
        self.client.logout()

    def test_delete_location(self):
        data = {"model_uuid": str(self.model.uuid), "location_id": self.location.id}
        response = self.client.post(reverse("delete_location"), data=data)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(json.loads(response.content), {"message": "deleted location"})


class AddTechnologyViewTestCase(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="my-username", email="my-email@example.com", password="my-password"
        )
        self.model = Model.objects.create(name="my-model")
        self.model_user = Model_User.objects.create(
            model=self.model, user=self.user, can_edit=True
        )
        self.abstract_tech = Abstract_Tech.objects.create(
            name="my-abstract-tech",
            pretty_name="MyAbstractTech",
            image="my-abstract-tech.png",
        )
        self.tech = Technology.objects.create(
            abstract_tech=self.abstract_tech,
            name="my-technology",
            pretty_name="MyTechnology",
            model=self.model,
        )
        self.param1 = Parameter.objects.create(
            root="root",
            category="public",
            name="my-param1",
            pretty_name="MyParam1",
            timeseries_enabled=True,
            choices=["c1", "c2"],
            units="kWh",
        )
        self.param2 = Parameter.objects.create(
            root="root",
            category="public",
            name="my-param2",
            pretty_name="MyParam2",
            timeseries_enabled=True,
            choices=["c1", "c2"],
            units="kWh",
        )

        self.tech_param = Tech_Param.objects.create(
            technology=self.tech, parameter=self.param1, model=self.model
        )
        
        self.tech_param = Tech_Param.objects.create(
            technology=self.tech, parameter=self.param2, model=self.model
        )
        self.client.login(username="my-username", password="my-password")

    def tearDown(self):
        self.client.logout()

    def test_add_technology(self):
        data = {
            "model_uuid": str(self.model.uuid),
            "technology_name": "my-technology",
            "technology_type": "my-abstract-tech",
        }
        response = self.client.post(reverse("add_technology"), data=data)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            json.loads(response.content),
            {"message": "added technology", "technology_id": self.tech.id + 1},
        )

        response = self.client.post(reverse("add_technology"), data=data)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            json.loads(response.content),
            {"message": "added technology", "technology_id": self.tech.id + 2},
        )


class DeleteTechnologyViewTestCase(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="my-username", email="my-email@example.com", password="my-password"
        )
        self.model = Model.objects.create(name="my-model")
        self.model_user = Model_User.objects.create(
            model=self.model, user=self.user, can_edit=True
        )
        self.abstract_tech = Abstract_Tech.objects.create(
            name="my-abstract-tech",
            pretty_name="MyAbstractTech",
            image="my-abstract-tech.png",
        )
        self.tech = Technology.objects.create(
            abstract_tech=self.abstract_tech,
            name="my-technology",
            pretty_name="MyTechnology",
            model=self.model,
        )
        self.client.login(username="my-username", password="my-password")

    def tearDown(self):
        self.client.logout()

    def test_delete_technology(self):
        data = {
            "model_uuid": str(self.model.uuid),
            "technology_id": 1,
        }
        response = self.client.post(reverse("delete_technology"), data=data)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            json.loads(response.content), {"message": "deleted technology"}
        )


class UpdateTechParamsViewTestCase(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="my-username", email="my-email@example.com", password="my-password"
        )
        self.model = Model.objects.create(name="my-model")
        self.model_user = Model_User.objects.create(
            model=self.model, user=self.user, can_edit=True
        )
        self.abstract_tech = Abstract_Tech.objects.create(
            name="my-abstract-tech",
            pretty_name="MyAbstractTech",
            image="my-abstract-tech.png",
        )
        self.tech = Technology.objects.create(
            abstract_tech=self.abstract_tech,
            name="my-technology",
            pretty_name="MyTechnology",
            model=self.model,
        )
        self.param = Parameter.objects.create(
            root="root",
            category="public",
            name="my-param-one",
            pretty_name="MyParamOne",
            timeseries_enabled=True,
            choices=["c1", "c2"],
            units="kWh",
        )
        self.tech_param = Tech_Param.objects.create(
            technology=self.tech, parameter=self.param, model=self.model
        )
        self.client.login(username="my-username", password="my-password")

    def tearDown(self):
        self.client.logout()

    def test_update_tech_params(self):
        data = {
            "model_uuid": str(self.model.uuid),
            "technology_id": self.tech.id,
            "form_data": json.dumps({}),
        }
        response = self.client.post(reverse("update_tech_params"), data=data)
        self.assertEqual(response.status_code, 200)


class UpdateFavoriteViewTestCase(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="my-username", email="my-email@example.com", password="my-password"
        )
        self.model = Model.objects.create(name="my-model")
        self.model_user = Model_User.objects.create(
            model=self.model, user=self.user, can_edit=True
        )
        self.param = Parameter.objects.create(
            root="root",
            category="public",
            name="my-param-one",
            pretty_name="MyParamOne",
            timeseries_enabled=True,
            choices=["c1", "c2"],
            units="kWh",
        )
        self.model_favorite = Model_Favorite.objects.create(
            model=self.model, parameter=self.param
        )
        self.client.login(username="my-username", password="my-password")

    def tearDown(self):
        self.client.logout()

    def test_update_favorite__add_favorite(self):
        data = {
            "model_uuid": str(self.model.uuid),
            "add_favorite": 1,
            "param_id": self.param.id,
        }
        response = self.client.get(reverse("update_favorite"), data=data)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(json.loads(response.content), {"message": "added favorite"})

    def test_update_favorite__remove_favorite(self):
        data = {
            "model_uuid": str(self.model.uuid),
            "add_favorite": 0,
            "param_id": self.param.id,
        }
        response = self.client.get(reverse("update_favorite"), data=data)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(json.loads(response.content), {"message": "removed favorite"})


class ConvertToTimeseriesViewTestCase(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="my-username", email="my-email@example.com", password="my-password"
        )
        self.model = Model.objects.create(name="my-model")
        self.model_user = Model_User.objects.create(
            model=self.model, user=self.user, can_edit=True
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
        self.abstract_tech = Abstract_Tech.objects.create(
            name="my-abstract-tech",
            pretty_name="MyAbstractTech",
            image="my-abstract-tech.png",
        )
        self.tech = Technology.objects.create(
            abstract_tech=self.abstract_tech,
            name="my-technology",
            pretty_name="MyTechnology",
            model=self.model,
        )
        self.loc_tech = Loc_Tech.objects.create(
            location_1=self.location1,
            location_2=self.location2,
            technology=self.tech,
            model=self.model,
        )
        self.param = Parameter.objects.create(
            root="root",
            category="public",
            name="my-param-one",
            pretty_name="MyParamOne",
            timeseries_enabled=True,
            choices=["c1", "c2"],
            units="kWh",
        )
        self.loc_tech_param = Loc_Tech_Param.objects.create(
            loc_tech=self.loc_tech, parameter=self.param, model=self.model
        )
        self.client.login(username="my-username", password="my-password")

    def tearDown(self):
        self.client.logout()

    def test_convert_to_timeseries__add_timeseries_to_node(self):
        data = {
            "model_uuid": str(self.model.uuid),
            "param_id": self.param.id,
            "technology_id": self.tech.id,
            "loc_tech_id": self.loc_tech.id,
        }
        response = self.client.get(reverse("convert_to_timeseries"), data=data)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            json.loads(response.content), {"message": "added timeseries to node"}
        )

    def test_convert_to_timeseries__add_timeseries_to_technology(self):
        data = {
            "model_uuid": str(self.model.uuid),
            "param_id": self.param.id,
            "technology_id": self.tech.id,
        }
        response = self.client.get(reverse("convert_to_timeseries"), data=data)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            json.loads(response.content), {"message": "added timeseries to technology"}
        )


class AddLocTechViewTestCase(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="my-username", email="my-email@example.com", password="my-password"
        )
        self.model = Model.objects.create(name="my-model")
        self.model_user = Model_User.objects.create(
            model=self.model, user=self.user, can_edit=True
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
        self.abstract_tech = Abstract_Tech.objects.create(
            name="my-abstract-tech",
            pretty_name="MyAbstractTech",
            image="my-abstract-tech.png",
        )
        self.tech = Technology.objects.create(
            abstract_tech=self.abstract_tech,
            name="my-technology",
            pretty_name="MyTechnology",
            model=self.model,
        )
        self.client.login(username="my-username", password="my-password")

    def tearDown(self):
        self.client.logout()

    def test_add_loc_tech(self):
        data = {
            "model_uuid": str(self.model.uuid),
            "technology_id": self.tech.id,
            "location_1_id": self.location1.id,
            "location_2_id": self.location2.id,
            "loc_tech_description": "this is loc-tech description",
        }
        response = self.client.post(reverse("add_loc_tech"), data=data)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            json.loads(response.content),
            {"message": "added location technology", "loc_tech_id": 1},
        )


class DeleteLocTechViewTestCase(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="my-username", email="my-email@example.com", password="my-password"
        )
        self.model = Model.objects.create(name="my-model")
        self.model_user = Model_User.objects.create(
            model=self.model, user=self.user, can_edit=True
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
        self.abstract_tech = Abstract_Tech.objects.create(
            name="my-abstract-tech",
            pretty_name="MyAbstractTech",
            image="my-abstract-tech.png",
        )
        self.tech = Technology.objects.create(
            abstract_tech=self.abstract_tech,
            name="my-technology",
            pretty_name="MyTechnology",
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

    def test_delete_loc_tech(self):
        data = {"model_uuid": str(self.model.uuid), "loc_tech_id": self.loc_tech.id}
        response = self.client.post(reverse("delete_loc_tech"), data=data)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            json.loads(response.content), {"message": "deleted location technology"}
        )


class UpdateLocTechParamsViewTestCase(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="my-username", email="my-email@example.com", password="my-password"
        )
        self.model = Model.objects.create(name="my-model")
        self.model_user = Model_User.objects.create(
            model=self.model, user=self.user, can_edit=True
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
        self.abstract_tech = Abstract_Tech.objects.create(
            name="my-abstract-tech",
            pretty_name="MyAbstractTech",
            image="my-abstract-tech.png",
        )
        self.tech = Technology.objects.create(
            abstract_tech=self.abstract_tech,
            name="my-technology",
            pretty_name="MyTechnology",
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

    def test_update_loc_tech_params(self):
        data = {
            "model_uuid": str(self.model.uuid),
            "loc_tech_id": self.loc_tech.id,
            "form_data": json.dumps({}),
        }
        response = self.client.post(reverse("update_loc_tech_params"), data=data)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(json.loads(response.content), {"message": "Success."})

        model_comments = Model_Comment.objects.all()
        self.assertEqual(len(model_comments), 1)


class AddScenarioViewTestCase(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="my-username", email="my-email@example.com", password="my-password"
        )
        self.model = Model.objects.create(name="my-model")
        self.model_user = Model_User.objects.create(
            model=self.model, user=self.user, can_edit=True
        )
        self.scenario = Scenario.objects.create(name="my-scenario", model=self.model)
        self.run_param = Run_Parameter.objects.create(
            root="root",
            name="my-run-parameter",
            pretty_name="MyRunParameter",
            user_visibility=True,
            default_value="default-run-param-value",
            choices=["c1", "c2"],
        )
        self.scenario_param = Scenario_Param.objects.create(
            scenario=self.scenario,
            run_parameter=self.run_param,
            value="scenario-param-default-value",
            model=self.model,
        )
        self.client.login(username="my-username", password="my-password")

    def tearDown(self):
        self.client.logout()

    def test_add_scenario__not_existing(self):
        data = {"model_uuid": str(self.model.uuid), "scenario_name": "my-new-scenario"}
        response = self.client.post(reverse("add_scenario"), data=data)
        self.assertEqual(response.status_code, 200)

        new_scenario = Scenario.objects.get(name="my-new-scenario")
        self.assertEqual(
            json.loads(response.content),
            {"message": "added scenario", "scenario_id": new_scenario.id},
        )

    def test_add_scenario__already_existing(self):
        data = {
            "model_uuid": str(self.model.uuid),
            "scenario_name": "another-scenario",
            "scenario_id": str(self.scenario.id),
        }
        response = self.client.post(reverse("add_scenario"), data=data)
        self.assertEqual(response.status_code, 200)

        new_scenario = Scenario.objects.get(name="another-scenario")
        self.assertEqual(
            json.loads(response.content),
            {"message": "added scenario", "scenario_id": new_scenario.id},
        )


class ToggleScenarioLocTechViewTestCase(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="my-username", email="my-email@example.com", password="my-password"
        )
        self.model = Model.objects.create(name="my-model")
        self.model_user = Model_User.objects.create(
            model=self.model, user=self.user, can_edit=True
        )
        self.scenario = Scenario.objects.create(name="my-scenario", model=self.model)
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
        self.abstract_tech = Abstract_Tech.objects.create(
            name="my-abstract-tech",
            pretty_name="MyAbstractTech",
            image="my-abstract-tech.png",
        )
        self.tech = Technology.objects.create(
            abstract_tech=self.abstract_tech,
            name="my-technology",
            pretty_name="MyTechnology",
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

    def test_toggle_scenario_loc_tech__not_add__not_scenario_loc_tech(self):
        data = {
            "model_uuid": str(self.model.uuid),
            "scenario_id": self.scenario.id,
            "loc_tech_id": 100,
            "add": 0,
        }
        response = self.client.post(reverse("toggle_scenario_loc_tech"), data=data)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            json.loads(response.content),
            {"message": "scenario location technology doesn' exist."},
        )

    def test_toggle_scenario_loc_tech__not_add__scenario_loc_tech(self):
        scenario_loc_tech = Scenario_Loc_Tech.objects.create(
            scenario=self.scenario, loc_tech=self.loc_tech, model=self.model
        )
        data = {
            "model_uuid": str(self.model.uuid),
            "scenario_id": self.scenario.id,
            "loc_tech_id": self.loc_tech.id,
            "add": 0,
        }
        response = self.client.post(reverse("toggle_scenario_loc_tech"), data=data)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            json.loads(response.content),
            {
                "message": "removed scenario location technology",
                "scenario_loc_tech_id": scenario_loc_tech.id,
            },
        )

    def test_toggle_scenario_loc_tech__add__not_scenario_loc_tech(self):
        data = {
            "model_uuid": str(self.model.uuid),
            "scenario_id": self.scenario.id,
            "loc_tech_id": self.loc_tech.id,
            "add": 1,
        }
        response = self.client.post(reverse("toggle_scenario_loc_tech"), data=data)
        self.assertEqual(response.status_code, 200)

        scenario_loc_tech = Scenario_Loc_Tech.objects.get(scenario=self.scenario)
        self.assertEqual(
            json.loads(response.content),
            {
                "message": "added scenario location technology",
                "scenario_loc_tech_id": scenario_loc_tech.id,
            },
        )

    def test_toggle_scenario_loc_tech__add__scenario_loc_tech(self):
        scenario_loc_tech = Scenario_Loc_Tech.objects.create(
            scenario=self.scenario, loc_tech=self.loc_tech, model=self.model
        )
        data = {
            "model_uuid": str(self.model.uuid),
            "scenario_id": self.scenario.id,
            "loc_tech_id": self.loc_tech.id,
            "add": 1,
        }
        response = self.client.post(reverse("toggle_scenario_loc_tech"), data=data)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            json.loads(response.content),
            {
                "message": "scenario location technology already exists",
                "scenario_loc_tech_id": scenario_loc_tech.id,
            },
        )


class UpdateScenarioParamsViewTestCase(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="my-username", email="my-email@example.com", password="my-password"
        )
        self.model = Model.objects.create(name="my-model")
        self.model_user = Model_User.objects.create(
            model=self.model, user=self.user, can_edit=True
        )
        self.scenario = Scenario.objects.create(name="my-scenario", model=self.model)
        self.run_param = Run_Parameter.objects.create(
            root="root",
            name="my-run-parameter",
            pretty_name="MyRunParameter",
            user_visibility=True,
            default_value="default-run-param-value",
            choices=["c1", "c2"],
        )
        self.scenario_param = Scenario_Param.objects.create(
            scenario=self.scenario,
            run_parameter=self.run_param,
            value="scenario-param-default-value",
            model=self.model,
        )
        self.client.login(username="my-username", password="my-password")

    def tearDown(self):
        self.client.logout()

    def test_update_scenario(self):
        data = {
            "model_uuid": str(self.model.uuid),
            "scenario_id": self.scenario.id,
            "form_data": json.dumps({}),
        }
        response = self.client.post(reverse("update_scenario"), data=data)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(json.loads(response.content), {"message": "Success."})


class DeleteScenarioViewTestCase(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="my-username", email="my-email@example.com", password="my-password"
        )
        self.model = Model.objects.create(name="my-model")
        self.model_user = Model_User.objects.create(
            model=self.model, user=self.user, can_edit=True
        )
        self.scenario = Scenario.objects.create(name="my-scenario", model=self.model)
        self.client.login(username="my-username", password="my-password")

    def tearDown(self):
        self.client.logout()

    def test_delete_scenario(self):
        data = {"model_uuid": str(self.model.uuid), "scenario_id": self.scenario.id}
        response = self.client.post(reverse("delete_scenario"), data=data)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(json.loads(response.content), {"message": "deleted scenario"})


class UploadFileViewTestCase(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="my-username", email="my-email@example.com", password="my-password"
        )
        self.model = Model.objects.create(name="my-model")
        self.model_user = Model_User.objects.create(
            model=self.model, user=self.user, can_edit=True
        )
        self.client.login(username="my-username", password="my-password")

    def tearDown(self):
        self.client.logout()

    def test_upload_file(self):
        myfile = SimpleUploadedFile(
            name="test-timeseries.csv",
            content=b"datetime,value\n20120101,100",
            content_type="text/plain",
        )
        data = {
            "model_uuid": str(self.model.uuid),
            "file-description": "this is file description.",
            "myfile": myfile,
        }
        response = self.client.post(reverse("upload_file"), data=data)
        self.assertEqual(response.status_code, 302)

        user_files = User_File.objects.all()
        self.assertEqual(len(user_files), 1)


class DeleteTimeseriesViewTestCase(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="my-username", email="my-email@example.com", password="my-password"
        )
        self.model = Model.objects.create(name="my-model")
        self.model_user = Model_User.objects.create(
            model=self.model, user=self.user, can_edit=True
        )
        self.timeseries_meta = Timeseries_Meta.objects.create(
            name="my-timeseries-meta", model=self.model
        )
        self.client.login(username="my-username", password="my-password")

    def tearDown(self):
        self.client.logout()

    def test_delete_timeseries(self):
        data = {
            "model_uuid": str(self.model.uuid),
            "timeseries_id": self.timeseries_meta.id,
        }
        response = self.client.post(reverse("delete_timeseries"), data=data)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(json.loads(response.content), {"message": "Success."})


class DeleteFileViewTestCase(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="my-username", email="my-email@example.com", password="my-password"
        )
        self.model = Model.objects.create(name="my-model")
        self.model_user = Model_User.objects.create(
            model=self.model, user=self.user, can_edit=True
        )
        self.user_file = User_File.objects.create(
            filename="my-timeseries-file", model=self.model
        )
        self.client.login(username="my-username", password="my-password")

    def tearDown(self):
        self.client.logout()

    def test_delete_file(self):
        data = {"model_uuid": str(self.model.uuid), "file_id": self.user_file.id}
        response = self.client.post(reverse("delete_file"), data=data)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(json.loads(response.content), {"message": "Success."})

        user_files = User_File.objects.all()
        self.assertEqual(len(user_files), 0)


class UploadTimeseriesViewTestCase(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="my-username", email="my-email@example.com", password="my-password"
        )
        self.model = Model.objects.create(name="my-model")
        self.model_user = Model_User.objects.create(
            model=self.model, user=self.user, can_edit=True
        )
        self.user_file = User_File.objects.create(
            filename="my-timeseries-file", model=self.model
        )
        self.timeseries_meta = Timeseries_Meta.objects.create(
            name="my-timeseries", model=self.model
        )
        self.client.login(username="my-username", password="my-password")

    def tearDown(self):
        self.client.logout()

    @staticmethod
    def get_async_result():
        result = MagicMock()
        result.id = str(uuid.uuid4())
        return result

    @patch("api.tasks.upload_ts")
    def test_upload_timeseries__existing(self, upload_ts):
        # GET vs POST
        upload_ts.side_effect = self.get_async_result()
        data = {
            "model_uuid": str(self.model.uuid),
            "file_id": self.user_file.id,
            "timeseries_name": "my-timeseries",
            "timestamp_col": 0,
            "value_col": 1,
            "has_header": False,
        }
        response = self.client.get(reverse("upload_timeseries"), data=data)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            json.loads(response.content),
            {"message": "Timeseries name already exists", "status": "FAILURE"},
        )

    @patch("api.tasks.upload_ts")
    def test_upload_timeseries__not_existing(self, upload_ts):
        # GET vs POST
        upload_ts.side_effect = self.get_async_result
        data = {
            "model_uuid": str(self.model.uuid),
            "file_id": self.user_file.id,
            "timeseries_name": "my-new-timeseries",
            "timestamp_col": 0,
            "value_col": 1,
            "has_header": False,
        }
        response = self.client.get(reverse("upload_timeseries"), data=data)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(json.loads(response.content), {"status": "Success"})
