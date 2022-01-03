"""
Unit tests for Django app "client" urls.
"""

import uuid

from django.conf import settings
from django.test import TestCase
from django.urls import reverse, resolve
from django.utils import translation


class ClientConfigurationComponentURLTestCase(TestCase):
    def test_all_tech_params(self):
        view_name = "all_tech_params"

        for language_code, _ in settings.LANGUAGES:
            with translation.override(language_code):
                url = f"/{language_code}/component/all_tech_params/"
                self.assertEqual(reverse(view_name), url)
                self.assertEqual(resolve(url).view_name, view_name)

    def test_all_loc_tech_params(self):
        view_name = "all_loc_tech_params"

        for language_code, _ in settings.LANGUAGES:
            with translation.override(language_code):
                url = f"/{language_code}/component/all_loc_tech_params/"
                self.assertEqual(reverse(view_name), url)
                self.assertEqual(resolve(url).view_name, view_name)

    def test_all_loc_techs(self):
        view_name = "all_loc_techs"

        for language_code, _ in settings.LANGUAGES:
            with translation.override(language_code):
                url = f"/{language_code}/component/all_loc_techs/"
                self.assertEqual(reverse(view_name), url)
                self.assertEqual(resolve(url).view_name, view_name)

    def test_location_coordinates(self):
        view_name = "location_coordinates"

        for language_code, _ in settings.LANGUAGES:
            with translation.override(language_code):
                url = f"/{language_code}/component/location_coordinates/"
                self.assertEqual(reverse(view_name), url)
                self.assertEqual(resolve(url).view_name, view_name)

    def test_timeseries_view(self):
        view_name = "timeseries_view"

        for language_code, _ in settings.LANGUAGES:
            with translation.override(language_code):
                url = f"/{language_code}/component/timeseries_view/"
                self.assertEqual(reverse(view_name), url)
                self.assertEqual(resolve(url).view_name, view_name)

    def test_timeseries_view(self):
        view_name = "timeseries_new"

        for language_code, _ in settings.LANGUAGES:
            with translation.override(language_code):
                url = f"/{language_code}/component/timeseries_new/"
                self.assertEqual(reverse(view_name), url)
                self.assertEqual(resolve(url).view_name, view_name)

    def test_timeseries_content(self):
        view_name = "timeseries_content"

        for language_code, _ in settings.LANGUAGES:
            with translation.override(language_code):
                url = f"/{language_code}/component/timeseries_content/"
                self.assertEqual(reverse(view_name), url)
                self.assertEqual(resolve(url).view_name, view_name)

    def test_scenario(self):
        view_name = "scenario"

        for language_code, _ in settings.LANGUAGES:
            with translation.override(language_code):
                url = f"/{language_code}/component/scenario/"
                self.assertEqual(reverse(view_name), url)
                self.assertEqual(resolve(url).view_name, view_name)


class ClientOutputsComponentURLTestCase(TestCase):
    def test_run_dashboard(self):
        view_name = "run_dashboard"

        for language_code, _ in settings.LANGUAGES:
            with translation.override(language_code):
                url = f"/{language_code}/component/run_dashboard/"
                self.assertEqual(reverse(view_name), url)
                self.assertEqual(resolve(url).view_name, view_name)

    def test_add_run_precheck(self):
        view_name = "add_run_precheck"

        for language_code, _ in settings.LANGUAGES:
            with translation.override(language_code):
                url = f"/{language_code}/component/add_run_precheck/"
                self.assertEqual(reverse(view_name), url)
                self.assertEqual(resolve(url).view_name, view_name)

    def test_plot_outputs(self):
        view_name = "plot_outputs"

        for language_code, _ in settings.LANGUAGES:
            with translation.override(language_code):
                url = f"/{language_code}/component/plot_outputs/"
                self.assertEqual(reverse(view_name), url)
                self.assertEqual(resolve(url).view_name, view_name)

    def test_map_outputs(self):
        view_name = "map_outputs"

        for language_code, _ in settings.LANGUAGES:
            with translation.override(language_code):
                url = f"/{language_code}/component/map_outputs/"
                self.assertEqual(reverse(view_name), url)
                self.assertEqual(resolve(url).view_name, view_name)


class ClientConfigurationURLTestCase(TestCase):
    def setUp(self):
        self.uuid = str(uuid.uuid4())

    def test_model(self):
        view_name = "model"

        for language_code, _ in settings.LANGUAGES:
            with translation.override(language_code):
                url = f"/{language_code}/{self.uuid}/model/"
                self.assertEqual(
                    reverse(view_name, kwargs={"model_uuid": self.uuid}), url
                )
                self.assertEqual(resolve(url).view_name, view_name)

    def test_parameters(self):
        view_name = "parameters"
        parameter_name = "my-param"

        for language_code, _ in settings.LANGUAGES:
            with translation.override(language_code):
                url = f"/{language_code}/{self.uuid}/parameters/{parameter_name}/"
                self.assertEqual(
                    reverse(
                        view_name,
                        kwargs={
                            "model_uuid": self.uuid,
                            "parameter_name": parameter_name,
                        },
                    ),
                    url,
                )
                self.assertEqual(resolve(url).view_name, view_name)

    def test_timeseries(self):
        view_name = "timeseries"

        for language_code, _ in settings.LANGUAGES:
            with translation.override(language_code):
                url = f"/{language_code}/{self.uuid}/timeseries/"
                self.assertEqual(
                    reverse(view_name, kwargs={"model_uuid": self.uuid}), url
                )
                self.assertEqual(resolve(url).view_name, view_name)

    def test_timeseries_table(self):
        view_name = "timeseries_table"

        for language_code, _ in settings.LANGUAGES:
            with translation.override(language_code):
                url = f"/{language_code}/{self.uuid}/timeseries_table/"
                self.assertEqual(
                    reverse(view_name, kwargs={"model_uuid": self.uuid}), url
                )
                self.assertEqual(resolve(url).view_name, view_name)

    def test_loc_techs(self):
        view_name = "loc_techs"

        for language_code, _ in settings.LANGUAGES:
            with translation.override(language_code):
                url = f"/{language_code}/{self.uuid}/loc_techs/"
                self.assertEqual(
                    reverse(view_name, kwargs={"model_uuid": self.uuid}), url
                )
                self.assertEqual(resolve(url).view_name, view_name)

    def test_locations(self):
        view_name = "locations"

        for language_code, _ in settings.LANGUAGES:
            with translation.override(language_code):
                url = f"/{language_code}/{self.uuid}/locations/"
                self.assertEqual(
                    reverse(view_name, kwargs={"model_uuid": self.uuid}), url
                )
                self.assertEqual(resolve(url).view_name, view_name)

    def test_technologies(self):
        view_name = "technologies"

        for language_code, _ in settings.LANGUAGES:
            with translation.override(language_code):
                url = f"/{language_code}/{self.uuid}/technologies/"
                self.assertEqual(
                    reverse(view_name, kwargs={"model_uuid": self.uuid}), url
                )
                self.assertEqual(resolve(url).view_name, view_name)

    def test_add_technologies(self):
        view_name = "add_technologies"

        for language_code, _ in settings.LANGUAGES:
            with translation.override(language_code):
                url = f"/{language_code}/{self.uuid}/add_technologies/"
                self.assertEqual(
                    reverse(view_name, kwargs={"model_uuid": self.uuid}), url
                )
                self.assertEqual(resolve(url).view_name, view_name)

    def test_scenarios(self):
        view_name = "scenarios"

        for language_code, _ in settings.LANGUAGES:
            with translation.override(language_code):
                url = f"/{language_code}/{self.uuid}/scenarios/"
                self.assertEqual(
                    reverse(view_name, kwargs={"model_uuid": self.uuid}), url
                )
                self.assertEqual(resolve(url).view_name, view_name)

    def test_add_scenarios(self):
        view_name = "add_scenarios"

        for language_code, _ in settings.LANGUAGES:
            with translation.override(language_code):
                url = f"/{language_code}/{self.uuid}/add_scenarios/"
                self.assertEqual(
                    reverse(view_name, kwargs={"model_uuid": self.uuid}), url
                )
                self.assertEqual(resolve(url).view_name, view_name)


class ClientOutputsURLTestCase(TestCase):
    def setUp(self):
        self.uuid = str(uuid.uuid4())

    def test_runs(self):
        view_name = "runs"

        for language_code, _ in settings.LANGUAGES:
            with translation.override(language_code):
                url = f"/{language_code}/{self.uuid}/runs/"
                self.assertEqual(
                    reverse(view_name, kwargs={"model_uuid": self.uuid}), url
                )
                self.assertEqual(resolve(url).view_name, view_name)

    def test_add_runs(self):
        view_name = "add_runs"
        scenario_id = 1

        for language_code, _ in settings.LANGUAGES:
            with translation.override(language_code):
                url = f"/{language_code}/{self.uuid}/add_runs/{scenario_id}/"
                self.assertEqual(
                    reverse(
                        view_name,
                        kwargs={
                            "model_uuid": self.uuid,
                            "scenario_id": scenario_id,
                        },
                    ),
                    url,
                )
                self.assertEqual(resolve(url).view_name, view_name)

    def test_map_viz(self):
        view_name = "map_viz"
        run_id = 1

        for language_code, _ in settings.LANGUAGES:
            with translation.override(language_code):
                url = f"/{language_code}/{self.uuid}/{run_id}/map_viz/"
                self.assertEqual(
                    reverse(
                        view_name,
                        kwargs={
                            "model_uuid": self.uuid,
                            "run_id": run_id,
                        },
                    ),
                    url,
                )
                self.assertEqual(resolve(url).view_name, view_name)


class ClientEngageURLTestCase(TestCase):
    
    def test_share(self):
        view_name = "settings"
        for language_code, _ in settings.LANGUAGES:
            with translation.override(language_code):
                url = f"/{language_code}/share/"
                self.assertEqual(reverse(view_name), url)
                self.assertEqual(resolve(url).view_name, view_name)

    def test_admin_login(self):
        view_name = "admin"
        for language_code, _ in settings.LANGUAGES:
            with translation.override(language_code):
                url = f"/{language_code}/admin/login/"
                self.assertEqual(reverse(view_name), url)
                self.assertEqual(resolve(url).view_name, view_name)
    
    def test_home(self):
        view_name = "home"
        for language_code, _ in settings.LANGUAGES:
            with translation.override(language_code):
                url = f"/{language_code}/"
                self.assertEqual(reverse(view_name), url)
                self.assertEqual(resolve(url).view_name, view_name)
