"""
Unit tests for Django app 'api' models - api/models/configuration.
"""
import datetime
import json
import uuid

from django.contrib.auth.models import User
from django.contrib.humanize.templatetags.humanize import ordinal
from django.forms.models import model_to_dict
from django.test import TestCase
from django.utils.safestring import SafeString

from api.models.calliope import Parameter, Abstract_Tech, Run_Parameter
from api.models.configuration import (
    # Models
    Model,
    Model_User,
    Model_Comment,
    Model_Favorite,
    User_File,
    Timeseries_Meta,
    Technology,
    Tech_Param,
    Location,
    Loc_Tech,
    Loc_Tech_Param,
    Scenario,
    Scenario_Loc_Tech,
    Scenario_Param,
    # Managers
    DuplicateModelManager,
    ParamsManager,
)
from api.exceptions import ModelAccessException


class ModelTestCase(TestCase):
    def setUp(self):
        self.model = Model.objects.create(name="my-model")
        self.user1 = User.objects.create_user(username="user1")
        self.user2 = User.objects.create_user(username="user2")
        self.model_user1 = Model_User.objects.create(model=self.model, user=self.user1)
        self.model_user2 = Model_User.objects.create(model=self.model, user=self.user2)
        self.guest = User.objects.create_user(username="guest")

    def test_class_meta(self):
        self.assertEqual(Model._meta.db_table, "model")
        self.assertEqual(Model._meta.verbose_name_plural, "[0] Models")

    def test_string_representation(self):
        self.assertEqual(str(self.model), self.model.name)

    def test_string_representation__snapshot_version(self):
        self.model.snapshot_version = 10
        self.model.save()
        self.assertEqual(
            str(self.model), f"{self.model.name} [v{self.model.snapshot_version}]"
        )

    def test_handle_edit_access__public_model__model_user(self):
        self.model.public = True
        self.model.save()
        with self.assertRaises(ModelAccessException):
            can_edit = self.model.handle_edit_access(user=self.user1)

    def test_handle_edit_access__private_model__model_user(self):
        self.model_user1.can_edit = True
        self.model_user1.save()
        can_edit = self.model.handle_edit_access(user=self.user1)
        self.assertTrue(can_edit)

    def test_handle_view_access__public_model__guest_user(self):
        self.model.public = True
        self.model.save()
        can_view = self.model.handle_view_access(user=self.guest)
        self.assertFalse(can_view)

    def test_handle_view_access__private_model__guest_user(self):
        with self.assertRaises(ModelAccessException):
            can_view = self.model.handle_view_access(user=self.guest)

    def test_handle_view_access__public_model__model_user(self):
        self.model.public = True
        self.model.save()
        can_view = self.model.handle_view_access(user=self.user1)
        self.assertFalse(can_view)

    def test_notify_collaborators(self):
        self.model.notify_collaborators(user=self.user1)
        self.model_user1.refresh_from_db()
        self.assertEqual(self.model_user1.notifications, 0)
        self.model_user2.refresh_from_db()
        self.assertEqual(self.model_user2.notifications, 1)

    def test_model_query(self):
        uuid1 = str(self.model.uuid)
        self.assertEqual(Model.by_uuid(uuid1), self.model)

    def test_carriers(self):
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
        param1 = Parameter.objects.create(
            root="root",
            category="public",
            name="my-param1",
            pretty_name="MyParam1",
            timeseries_enabled=True,
            choices=["c1", "c2"],
            units="kWh",
        )
        param2 = Parameter.objects.create(
            root="root",
            category="public",
            name="my-param2",
            pretty_name="MyParam2",
            timeseries_enabled=True,
            choices=["c1", "c2"],
            units="kWh",
        )
        param3 = Parameter.objects.create(
            root="root",
            category="public",
            name="my-para3",
            pretty_name="MyParam3",
            timeseries_enabled=True,
            choices=["c1", "c2"],
            units="kWh",
        )
        param4 = Parameter.objects.create(
            root="root",
            category="public",
            name="my-param4",
            pretty_name="MyParam4",
            timeseries_enabled=True,
            choices=["c1", "c2"],
            units="kWh",
        )
        tech_param = Tech_Param.objects.create(
            technology=tech, parameter=param4, model=self.model
        )
        self.assertEqual(len(self.model.carriers), 0)

    def test_favorites(self):
        param = Parameter.objects.create(
            root="root",
            category="public",
            name="my-param-one",
            pretty_name="MyParamOne",
            timeseries_enabled=True,
            choices=["c1", "c2"],
            units="kWh",
        )
        model_favorite = Model_Favorite.objects.create(
            model=self.model, parameter=param
        )
        self.assertEqual(len(self.model.favorites), 1)

    def test_collaborators(self):
        self.assertEqual(len(self.model.collaborators()), 2)

    def test_deprecate_runs(self):
        self.assertEqual(self.model.deprecate_runs(), True)
    
    def test_deprecate_runs__scenario(self):
        scenario = Scenario.objects.create(name="my-scenario", model=self.model)
        self.assertEqual(self.model.deprecate_runs(scenario_id=scenario.id), True)

    def test_deprecate_runs__loc_techs(self):
        location1 = Location.objects.create(
            name="my-location-one",
            pretty_name="MyLocationOne",
            latitude=40.1,
            longitude=-108.2,
            model=self.model,
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
            model=self.model,
            pretty_tag="MyPrettyTag"
        )
        loc_tech = Loc_Tech.objects.create(
            location_1=location1, technology=tech, model=self.model
        )
        self.assertEqual(self.model.deprecate_runs(location_id=location1.id), True)
        self.assertEqual(self.model.deprecate_runs(technology_id=tech.id), True)

    def test_duplicate(self):
        self.model.duplicate(is_snapshot=False)
        self.assertEqual(len(Model.objects.all()), 2)


class ModelUserTestCase(TestCase):
    def setUp(self):
        self.model = Model.objects.create(name="my-model")
        self.user = User.objects.create_user(username="test_user")
        self.model_user = Model_User.objects.create(model=self.model, user=self.user)

    def test_class_meta(self):
        self.assertEqual(Model_User._meta.db_table, "model_user")
        self.assertEqual(Model_User._meta.verbose_name_plural, "[0] Model Users")

    def test_string_representation(self):
        self.assertEqual(str(self.model_user), f"{str(self.model)} - {str(self.user)}")

    def test_update__model_existing(self):
        self.assertFalse(self.model_user.can_edit)
        message = Model_User.update(model=self.model, user=self.user, can_edit=True)
        self.model_user.refresh_from_db()
        self.assertTrue(self.model_user.can_edit)
        self.assertEqual(message, "Updated collaborator.")

    def test_update__model_not_existing(self):
        user2 = User.objects.create_user(
            username="user2", email="user2-email@example.com", password="user2-password"
        )
        model2 = Model.objects.create(name="my-model2")
        message = Model_User.update(model=model2, user=user2, can_edit=False)
        self.assertEqual(message, "Added collaborator.")


class ModelCommentTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        model = Model.objects.create(name="my-model")
        user = User.objects.create_user(username="test_user")
        cls.model_comment = Model_Comment.objects.create(
            user=user, model=model, comment="<p>this is a comment.</p>"
        )

    def test_class_meta(self):
        self.assertEqual(Model_Comment._meta.db_table, "model_comment")
        self.assertEqual(Model_Comment._meta.verbose_name_plural, "[0] Model Comments")

    def test_string_representation(self):
        self.assertEqual(str(self.model_comment), self.model_comment.comment)

    def safe_comment(self):
        self.assertIsInstance(self.model_comment(), SafeString)

    def test_icon__edit(self):
        self.model_comment.type = "edit"
        self.assertIsInstance(self.model_comment.icon(), SafeString)

    def test_icon__uknown(self):
        self.model_comment.type = "unknown"
        self.assertEqual(self.model_comment.icon(), "")


class ModelFavoriteTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        model = Model.objects.create(name="my-model")
        param = Parameter.objects.create(
            root="root",
            category="public",
            name="my-param-one",
            pretty_name="MyParamOne",
            timeseries_enabled=True,
            choices=["c1", "c2"],
            units="kWh",
        )
        cls.model_favorite = Model_Favorite.objects.create(model=model, parameter=param)

    def test_class_meta(self):
        self.assertEqual(Model_Favorite._meta.db_table, "model_favorite")
        self.assertEqual(
            Model_Favorite._meta.verbose_name_plural, "[0] Model Favorites"
        )

    def test_string_representation(self):
        self.assertEqual(
            str(self.model_favorite),
            f"{self.model_favorite.model} - {self.model_favorite.parameter}",
        )


class UserFileTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        model = Model.objects.create(name="my-model")
        cls.user_file = User_File.objects.create(
            filename="user_files/test.csv", model=model
        )

    def test_class_meta(self):
        self.assertEqual(User_File._meta.db_table, "user_file")
        self.assertEqual(User_File._meta.verbose_name_plural, "[0] User File Uploads")

    def test_simple_filename(self):
        self.assertEqual(self.user_file.simple_filename(), "test.csv")


class TimeseriesMetaTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        model = Model.objects.create(name="my-model")
        cls.timeseries_meta = Timeseries_Meta.objects.create(
            name="my-timeseries-meta", model=model
        )

    def test_class_meta(self):
        self.assertEqual(Timeseries_Meta._meta.db_table, "timeseries_meta")
        self.assertEqual(
            Timeseries_Meta._meta.verbose_name_plural, "[3] Timeseries Meta"
        )

    def test_string_representation__no_original_filename(self):
        self.assertEqual(str(self.timeseries_meta), self.timeseries_meta.name)

    def test_string_representation__original_filename(self):
        self.timeseries_meta.original_filename = "test.csv"
        self.timeseries_meta.original_value_col = 1
        self.timeseries_meta.save()

        s = "{} - {} (2nd column)".format(
            self.timeseries_meta.name,
            self.timeseries_meta.original_filename
        )
        self.assertEqual(str(self.timeseries_meta), s)


class TechnologyTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        abstract_tech = Abstract_Tech.objects.create(
            name="my-abstract-tech",
            pretty_name="MyAbstractTech",
            image="my-abstract-tech.png",
        )
        cls.model = Model.objects.create(name="my-model")
        cls.tech = Technology.objects.create(
            abstract_tech=abstract_tech,
            name="my-technology",
            pretty_name="MyTechnology",
            model=cls.model,
        )

    def test_class_meta(self):
        self.assertEqual(Technology._meta.db_table, "technology")
        self.assertEqual(Technology._meta.verbose_name_plural, "[2] Technologies")

    def test_string_representation(self):
        self.assertEqual(str(self.tech), self.tech.pretty_name)

    def test_calliope_name__no_tag(self):
        self.assertEqual(self.tech.calliope_name, self.tech.name)

    def test_calliope_name__tag(self):
        self.tech.tag = "my-tech-tag"
        s = "{}-{}".format(self.tech.name, self.tech.tag)
        self.assertEqual(self.tech.calliope_name, s)

    def test_color__no_tech_param(self):
        self.assertEqual(self.tech.color, "white")

    def test_color__with_tech_param(self):
        param = Parameter.objects.create(
            root="root",
            category="public",
            name="color",
            pretty_name="MyParamOne",
            timeseries_enabled=True,
            choices=["c1", "c2"],
            units="kWh",
        )
        tech_param = Tech_Param.objects.create(
            technology=self.tech, parameter=param, model=self.model, value="my-color"
        )
        self.assertEqual(self.tech.color, tech_param.value)

    def test_carrier_in(self):
        carrier = Parameter.objects.create(
            root="root",
            category="public",
            name="carrier",
            pretty_name="MyCarrier",
            timeseries_enabled=True,
            choices=["c1", "c2"],
            units="kWh",
        )
        carrier_tech_param = Tech_Param.objects.create(
            technology=self.tech, parameter=carrier, model=self.model, value="my-carrier"
        )
        carrier_in3 = Parameter.objects.create(
            root="root",
            category="public",
            name="carrier_in_3",
            pretty_name="MyCarrierOut3",
            timeseries_enabled=True,
            choices=["c1", "c2"],
            units="kWh",
        )
        carrier_in3_tech_param = Tech_Param.objects.create(
            technology=self.tech,
            parameter=carrier_in3,
            model=self.model,
            value="my-carrier-in3",
        )
        self.assertEqual(self.tech.carrier_in, "my-carrier,my-carrier-in3")

    def test_carrier_out(self):
        carrier = Parameter.objects.create(
            root="root",
            category="public",
            name="carrier",
            pretty_name="MyCarrier",
            timeseries_enabled=True,
            choices=["c1", "c2"],
            units="kWh",
        )
        carrier_tech_param = Tech_Param.objects.create(
            technology=self.tech, parameter=carrier, model=self.model, value="my-carrier"
        )
        carrier_out3 = Parameter.objects.create(
            root="root",
            category="public",
            name="carrier_out_3",
            pretty_name="MyCarrierOut3",
            timeseries_enabled=True,
            choices=["c1", "c2"],
            units="kWh",
        )
        carrier_out3_tech_param = Tech_Param.objects.create(
            technology=self.tech,
            parameter=carrier_out3,
            model=self.model,
            value="my-carrier-out3",
        )
        self.assertEqual(self.tech.carrier_out, "my-carrier,my-carrier-out3")

    def test_to_dict(self):
        self.assertTrue("model" in self.tech.to_dict())

    def test_to_json(self):
        self.assertTrue("model" in json.loads(self.tech.to_json()))

    def color__default(self):
        self.assertEqual(self.tech.color, "#fff")

    def color__custom(self):
        color_param1 = Parameter.objects.create(
            root="root",
            category="public",
            name="color",
            pretty_name="MyColor1",
            timeseries_enabled=True,
            choices=["c1", "c2"],
            units="kWh",
        )
        color_param2 = Parameter.objects.create(
            root="root",
            category="public",
            name="color",
            pretty_name="MyColor2",
            timeseries_enabled=True,
            choices=["c1", "c2"],
            units="kWh",
        )
        color_param3 = Parameter.objects.create(
            root="root",
            category="public",
            name="color",
            pretty_name="MyColor3",
            timeseries_enabled=True,
            choices=["c1", "c2"],
            units="kWh",
        )
        arrier_tech_param = Tech_Param.objects.create(
            technology=self.tech, parameter=color_param3, model=self.model, value="my-color3"
        )
        self.assertEqual(self.tech.color, "my-color3")

    def test_duplicate(self):
        new_tech = self.tech.duplicate(model_id=self.model.id, pretty_name="NewTechName")
        self.assertEqual(new_tech.pretty_name, "NewTechName")

    def test_update(self):
        form_data = {"is_linear": False, "is_expansion": False}
        self.tech.update(form_data)
        self.assertEqual(self.tech.is_linear, False)
        self.assertEqual(self.tech.is_expansion, False)


class TechParamTestCase(TestCase):
    def setUp(self):
        abstract_tech = Abstract_Tech.objects.create(
            name="my-abstract-tech",
            pretty_name="MyAbstractTech",
            image="my-abstract-tech.png",
        )
        model = Model.objects.create(name="my-model")
        tech = Technology.objects.create(
            abstract_tech=abstract_tech,
            name="my-technology",
            pretty_name="MyTechnology",
            model=model,
        )
        param = Parameter.objects.create(
            root="root",
            category="public",
            name="my-param-one",
            pretty_name="MyParamOne",
            timeseries_enabled=True,
            choices=["c1", "c2"],
            units="kWh",
        )
        self.tech_param = Tech_Param.objects.create(
            technology=tech, parameter=param, model=model
        )

    def test_class_meta(self):
        self.assertEqual(Tech_Param._meta.db_table, "tech_param")
        self.assertEqual(
            Tech_Param._meta.verbose_name_plural, "[2] Technology Parameters"
        )
    
    def test__essentials(self):
        pass
    
    def test__cplus_carriers(self):
        pass
    
    def test__add(self):
        pass
    
    def test__edit(self):
        pass
    
    def test__delete(self):
        pass
    

class LocationTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        model = Model.objects.create(name="my-model")
        cls.location = Location.objects.create(
            name="my-location",
            pretty_name="MyLocation",
            latitude=40.1,
            longitude=-108.2,
            model=model,
        )

    def test_class_meta(self):
        self.assertEqual(Location._meta.db_table, "location")
        self.assertEqual(Location._meta.verbose_name_plural, "[1] Locations")

    def test_string_representation(self):
        self.assertEqual(str(self.location), self.location.pretty_name)


class LocTechTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.model = Model.objects.create(name="my-model")
        location1 = Location.objects.create(
            name="my-location-one",
            pretty_name="MyLocationOne",
            latitude=40.1,
            longitude=-108.2,
            model=cls.model,
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
            model=cls.model,
            pretty_tag="MyPrettyTag"
        )
        cls.loc_tech = Loc_Tech.objects.create(
            location_1=location1, technology=tech, model=cls.model
        )

    def test_class_meta(self):
        self.assertEqual(Loc_Tech._meta.db_table, "loc_tech")
        self.assertEqual(
            Loc_Tech._meta.verbose_name_plural, "[3] Location Technologies"
        )

    def test_string_representation__no_location2(self):
        s = "{} | {} [{}]".format(
            self.loc_tech.location_1,
            self.loc_tech.technology,
            self.loc_tech.technology.pretty_tag
        )
        self.assertEqual(str(self.loc_tech), s)
    
    def test_string_representation__with_location2(self):
        location2 = Location.objects.create(
            name="my-location-two",
            pretty_name="MyLocationTwo",
            latitude=41.5,
            longitude=-107.1,
            model=self.model,
        )
        self.loc_tech.location_2 = location2
        self.loc_tech.save()
        s = "{} <-> {} | {} [{}]".format(
            self.loc_tech.location_1,
            self.loc_tech.location_2,
            self.loc_tech.technology,
            self.loc_tech.technology.pretty_tag
        )
        self.assertEqual(str(self.loc_tech), s)


class LocTechParamTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        model = Model.objects.create(name="my-model")
        location1 = Location.objects.create(
            name="my-location-one",
            pretty_name="MyLocationOne",
            latitude=40.1,
            longitude=-108.2,
            model=model,
        )
        location2 = Location.objects.create(
            name="my-location-two",
            pretty_name="MyLocationTwo",
            latitude=41.5,
            longitude=-107.1,
            model=model,
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
        loc_tech = Loc_Tech.objects.create(
            location_1=location1, location_2=location2, technology=tech, model=model
        )
        param = Parameter.objects.create(
            root="root",
            category="public",
            name="my-param-one",
            pretty_name="MyParamOne",
            timeseries_enabled=True,
            choices=["c1", "c2"],
            units="kWh",
        )
        cls.loc_tech_param = Loc_Tech_Param.objects.create(
            loc_tech=loc_tech, parameter=param, model=model
        )

    def test_class_meta(self):
        self.assertEqual(Loc_Tech_Param._meta.db_table, "loc_tech_param")
        self.assertEqual(
            Loc_Tech_Param._meta.verbose_name_plural,
            "[3] Location Technology Parameters",
        )
    
    def test__add(self):
        pass
    
    def test__edit(self):
        pass
    
    def test__delete(self):
        pass


class ScenarioTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.model = Model.objects.create(name="my-model")
        cls.scenario = Scenario.objects.create(name="my-scenario", model=cls.model)

    def test_class_meta(self):
        self.assertEqual(Scenario._meta.db_table, "scenario")
        self.assertEqual(Scenario._meta.verbose_name_plural, "[4] Scenarios")

    def test_string_representation(self):
        self.assertEqual(str(self.scenario), self.scenario.name)

    def test_duplicate(self):
        new_scenario = self.scenario.duplicate(name="NewScenario")
        self.assertEqual(len(Scenario.objects.all()), 2)

    def test_timeseries_precheck(self):
        timeseries_meta = Timeseries_Meta.objects.create(
            name="my-timeseries-meta", model=self.model,
            start_date="2015-01-01",
            end_date="2015-01-02"
        )
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
        param = Parameter.objects.create(
            root="root",
            category="public",
            name="my-param-one",
            pretty_name="MyParamOne",
            timeseries_enabled=True,
            choices=["c1", "c2"],
            units="kWh",
        )
        tech_param = Tech_Param.objects.create(
            technology=tech, parameter=param, model=self.model,
            timeseries_meta=timeseries_meta, timeseries=True
        )
        loc_tech = Loc_Tech.objects.create(
            location_1=location1, location_2=location2, technology=tech, model=self.model
        )
        loc_tech_param = Loc_Tech_Param.objects.create(
            loc_tech=loc_tech, parameter=param, model=self.model,
            timeseries_meta=timeseries_meta, timeseries=True
        )
        scenario_loc_tech = Scenario_Loc_Tech.objects.create(
            scenario=self.scenario, loc_tech=loc_tech, model=self.model
        )
        ts_params, missing_ts = self.scenario.timeseries_precheck()
        self.assertEqual(json.loads(ts_params), [['MyLocationOne <-> MyLocationTwo | MyTechnology [None]', 'MyParamOne', '01/01/2015, 00:00:00', '01/02/2015, 00:00:00']])
        self.assertEqual(missing_ts, set())

class ScenarioLocTechTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        model = Model.objects.create(name="my-model")
        scenario = Scenario.objects.create(name="my-scenario", model=model)
        location1 = Location.objects.create(
            name="my-location-one",
            pretty_name="MyLocationOne",
            latitude=40.1,
            longitude=-108.2,
            model=model,
        )
        location2 = Location.objects.create(
            name="my-location-two",
            pretty_name="MyLocationTwo",
            latitude=41.5,
            longitude=-107.1,
            model=model,
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
        loc_tech = Loc_Tech.objects.create(
            location_1=location1, location_2=location2, technology=tech, model=model
        )
        cls.scenario_loc_tech = Scenario_Loc_Tech.objects.create(
            scenario=scenario, loc_tech=loc_tech, model=model
        )

    def test_class_meta(self):
        self.assertEqual(Scenario_Loc_Tech._meta.db_table, "scenario_loc_tech")
        self.assertEqual(
            Scenario_Loc_Tech._meta.verbose_name_plural,
            "[4] Scenario Location Technologies",
        )

    def test_string_representation(self):
        self.assertEqual(
            str(self.scenario_loc_tech), str(self.scenario_loc_tech.loc_tech)
        )


class ScenarioParamTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        model = Model.objects.create(name="my-model")
        cls.scenario = Scenario.objects.create(name="my-scenario", model=model)
        run_param = Run_Parameter.objects.create(
            root="root",
            name="my-run-parameter",
            pretty_name="MyRunParameter",
            user_visibility=True,
            default_value="default-run-param-value",
            choices=["c1", "c2"],
        )
        cls.scenario_param = Scenario_Param.objects.create(
            scenario=cls.scenario,
            run_parameter=run_param,
            value="scenario-param-default-value",
            model=model,
        )

    def test_class_meta(self):
        self.assertEqual(Scenario_Param._meta.db_table, "scenario_param")
        self.assertEqual(
            Scenario_Param._meta.verbose_name_plural, "[4] Scenario Parameters"
        )

    def test_update(self):
        pass
    
    def test__add(self):
        pass
    
    def test__edit(self):
        pass
    
    def test__delete(self):
        pass
    
    def test__int_or_zero(self):
        pass


class ParamsManagerTestCase(TestCase):
    
    def test_all_tech_params(self):
        pass
    
    def test_all_loc_tech_params(self):
        pass
    
    def test_get_tech_params_dict(self):
        pass
    
    def test_parse_essentials(self):
        pass
    
    def test_simplify_name(self):
        pass
