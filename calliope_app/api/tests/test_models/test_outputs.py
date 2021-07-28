"""
Unit tests for Django app 'api' models - api/models/configuration.
"""

from django.test import TestCase

from api.models.outputs import Run
from api.models.configuration import Model, Scenario


class RunTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.model = Model.objects.create(name="my-model")
        cls.scenario = Scenario.objects.create(
            name="my-scenario", model=cls.model, description="my-scenario-description"
        )
        cls.model_run = Run.objects.create(
            scenario=cls.scenario,
            subset_time="2015-01-0--2015-01-02",
            year=2015,
            status="QUEUED",
            message="run message",
            inputs_path="/this/is/inputs",
            logs_path="/this/is/logs.html",
            outputs_path="/this/is/outputs",
            plots_path="/this/is/plots.html",
            model=cls.model,
            description="my-run-description",
        )

    def test_class_meta(self):
        self.assertEqual(Run._meta.db_table, "run")
        self.assertEqual(Run._meta.verbose_name_plural, "[5] Runs")

    def test_string_representation(self):
        self.assertIn(
            f"{self.model_run.model} ({self.model_run.subset_time})",
            str(self.model_run),
        )
