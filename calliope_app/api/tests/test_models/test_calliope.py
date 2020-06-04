"""
Unit tests for Django app 'api' models - api/models/calliope
"""

from django.test import TestCase

from api.models.calliope import (
    Parameter,
    Abstract_Tech,
    Abstract_Tech_Param,
    Run_Parameter,
)


class ParameterTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.param = Parameter.objects.create(
            root="root",
            category="public",
            name="my_param_one",
            pretty_name="MyParamOne",
            timeseries_enabled=True,
            choices=["c1", "c2"],
            units="kWh",
        )

    def test_class_meta(self):
        self.assertEqual(Parameter._meta.db_table, "parameter")
        self.assertEqual(Parameter._meta.verbose_name_plural, "[Admin] Parameters")

    def test_string_representation(self):
        self.assertEqual(str(self.param), self.param.pretty_name)


class AbstractTechTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.abstract_tech = Abstract_Tech.objects.create(
            name="my-abstract-tech",
            pretty_name="MyAbstractTech",
            image="my-abstract-tech.png",
        )

    def test_class_meta(self):
        self.assertEqual(Abstract_Tech._meta.db_table, "abstract_tech")
        self.assertEqual(
            Abstract_Tech._meta.verbose_name_plural, "[Admin] Abstract Technologies"
        )

    def test_string_representation(self):
        self.assertEqual(
            str(self.abstract_tech),
            f"{self.abstract_tech.pretty_name} ({self.abstract_tech.name})",
        )


class AbstractTechParamTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        param = Parameter.objects.create(
            root="root",
            category="public",
            name="my-param-one",
            pretty_name="MyParamOne",
            timeseries_enabled=True,
            choices=["c1", "c2"],
            units="kWh",
        )
        abstract_tech = Abstract_Tech.objects.create(
            name="my-abstract-tech",
            pretty_name="MyAbstractTech",
            image="my-abstract-tech.png",
        )
        Abstract_Tech_Param.objects.create(
            abstract_tech=abstract_tech,
            parameter=param,
            default_value="default-tech-param-value",
        )

    def test_class_meta(self):
        self.assertEqual(Abstract_Tech_Param._meta.db_table, "abstract_tech_param")
        self.assertEqual(
            Abstract_Tech_Param._meta.verbose_name_plural,
            "[Admin] Abstract Technology Parameters",
        )


class RunParameterTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.run_param = Run_Parameter.objects.create(
            root="root",
            name="my-run-parameter",
            pretty_name="MyRunParameter",
            user_visibility=True,
            default_value="default-run-param-value",
            choices=["c1", "c2"],
        )

    def test_class_meta(self):
        self.assertEqual(Run_Parameter._meta.db_table, "run_parameter")
        self.assertEqual(
            Run_Parameter._meta.verbose_name_plural, "[Admin] Run Parameters"
        )

    def test_string_representation(self):
        self.assertEqual(str(self.run_param), self.run_param.pretty_name)
