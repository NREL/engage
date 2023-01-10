"""
Unit tests for Django app "api" urls.
"""
from django.conf import settings
from django.test import TestCase
from django.urls import reverse, resolve
from django.utils import translation


class APIModelURLTestCase(TestCase):
    def test_add_model(self):
        view_name = "add_model"

        for language_code, _ in settings.LANGUAGES:
            with translation.override(language_code):
                url = f"/{language_code}/api/add_model/"
                self.assertEqual(reverse(view_name), url)
                self.assertEqual(resolve(url).view_name, view_name)

    def test_remove_model(self):
        view_name = "remove_model"

        for language_code, _ in settings.LANGUAGES:
            with translation.override(language_code):
                url = f"/{language_code}/api/remove_model/"
                self.assertEqual(reverse(view_name), url)
                self.assertEqual(resolve(url).view_name, view_name)

    def test_duplicate_model(self):
        view_name = "duplicate_model"

        for language_code, _ in settings.LANGUAGES:
            with translation.override(language_code):
                url = f"/{language_code}/api/duplicate_model/"
                self.assertEqual(reverse(view_name), url)
                self.assertEqual(resolve(url).view_name, view_name)

    def test_add_collaborator(self):
        view_name = "add_collaborator"

        for language_code, _ in settings.LANGUAGES:
            with translation.override(language_code):
                url = f"/{language_code}/api/add_collaborator/"
                self.assertEqual(reverse(view_name), url)
                self.assertEqual(resolve(url).view_name, view_name)

    def testt_add_model_comment(self):
        view_name = "add_model_comment"

        for language_code, _ in settings.LANGUAGES:
            with translation.override(language_code):
                url = f"/{language_code}/api/add_model_comment/"
                self.assertEqual(reverse(view_name), url)
                self.assertEqual(resolve(url).view_name, view_name)


class APILocationURLTestCase(TestCase):
    def test_update_location(self):
        view_name = "update_location"

        for language_code, _ in settings.LANGUAGES:
            with translation.override(language_code):
                url = f"/{language_code}/api/update_location/"
                self.assertEqual(reverse(view_name), url)
                self.assertEqual(resolve(url).view_name, view_name)

    def test_delete_location(self):
        view_name = "delete_location"

        for language_code, _ in settings.LANGUAGES:
            with translation.override(language_code):
                url = f"/{language_code}/api/delete_location/"
                self.assertEqual(reverse(view_name), url)
                self.assertEqual(resolve(url).view_name, view_name)


class APIParameterURLTestCase(TestCase):
    def test_convert_to_timeseries(self):
        view_name = "convert_to_timeseries"

        for language_code, _ in settings.LANGUAGES:
            with translation.override(language_code):
                url = f"/{language_code}/api/convert_to_timeseries/"
                self.assertEqual(reverse(view_name), url)
                self.assertEqual(resolve(url).view_name, view_name)

    def test_update_favorite(self):
        view_name = "update_favorite"

        for language_code, _ in settings.LANGUAGES:
            with translation.override(language_code):
                url = f"/{language_code}/api/update_favorite/"
                self.assertEqual(reverse(view_name), url)
                self.assertEqual(resolve(url).view_name, view_name)


class APITechnologyURLTestCase(TestCase):
    def test_add_technology(self):
        view_name = "add_technology"

        for language_code, _ in settings.LANGUAGES:
            with translation.override(language_code):
                url = f"/{language_code}/api/add_technology/"
                self.assertEqual(reverse(view_name), url)
                self.assertEqual(resolve(url).view_name, view_name)

    def test_delete_technology(self):
        view_name = "delete_technology"

        for language_code, _ in settings.LANGUAGES:
            with translation.override(language_code):
                url = f"/{language_code}/api/delete_technology/"
                self.assertEqual(reverse(view_name), url)
                self.assertEqual(resolve(url).view_name, view_name)

    def test_update_tech_params(self):
        view_name = "update_tech_params"

        for language_code, _ in settings.LANGUAGES:
            with translation.override(language_code):
                url = f"/{language_code}/api/update_tech_params/"
                self.assertEqual(reverse(view_name), url)
                self.assertEqual(resolve(url).view_name, view_name)


class APILocTechURLTestCase(TestCase):
    def test_add_loc_tech(self):
        view_name = "add_loc_tech"

        for language_code, _ in settings.LANGUAGES:
            with translation.override(language_code):
                url = f"/{language_code}/api/add_loc_tech/"
                self.assertEqual(reverse(view_name), url)
                self.assertEqual(resolve(url).view_name, view_name)

    def test_delete_loc_tech(self):
        view_name = "delete_loc_tech"

        for language_code, _ in settings.LANGUAGES:
            with translation.override(language_code):
                url = f"/{language_code}/api/delete_loc_tech/"
                self.assertEqual(reverse(view_name), url)
                self.assertEqual(resolve(url).view_name, view_name)

    def test_update_loc_tech_params(self):
        view_name = "update_loc_tech_params"

        for language_code, _ in settings.LANGUAGES:
            with translation.override(language_code):
                url = f"/{language_code}/api/update_loc_tech_params/"
                self.assertEqual(reverse(view_name), url)
                self.assertEqual(resolve(url).view_name, view_name)


class APIScenarioURLTestCase(TestCase):
    def test_add_scenario(self):
        view_name = "add_scenario"

        for language_code, _ in settings.LANGUAGES:
            with translation.override(language_code):
                url = f"/{language_code}/api/add_scenario/"
                self.assertEqual(reverse(view_name), url)
                self.assertEqual(resolve(url).view_name, view_name)

    def test_toggle_scenario_loc_tech(self):
        view_name = "toggle_scenario_loc_tech"

        for language_code, _ in settings.LANGUAGES:
            with translation.override(language_code):
                url = f"/{language_code}/api/toggle_scenario_loc_tech/"
                self.assertEqual(reverse(view_name), url)
                self.assertEqual(resolve(url).view_name, view_name)

    def test_update_scenario_params(self):
        view_name = "update_scenario_params"

        for language_code, _ in settings.LANGUAGES:
            with translation.override(language_code):
                url = f"/{language_code}/api/update_scenario_params/"
                self.assertEqual(reverse(view_name), url)
                self.assertEqual(resolve(url).view_name, view_name)

    def test_delete_scenario(self):
        view_name = "delete_scenario"

        for language_code, _ in settings.LANGUAGES:
            with translation.override(language_code):
                url = f"/{language_code}/api/delete_scenario/"
                self.assertEqual(reverse(view_name), url)
                self.assertEqual(resolve(url).view_name, view_name)


class APIFileURLTestCase(TestCase):
    def test_upload_file(self):
        view_name = "upload_file"

        for language_code, _ in settings.LANGUAGES:
            with translation.override(language_code):
                url = f"/{language_code}/api/upload_file/"
                self.assertEqual(reverse(view_name), url)
                self.assertEqual(resolve(url).view_name, view_name)

    def test_delete_file(self):
        view_name = "delete_file"

        for language_code, _ in settings.LANGUAGES:
            with translation.override(language_code):
                url = f"/{language_code}/api/delete_file/"
                self.assertEqual(reverse(view_name), url)
                self.assertEqual(resolve(url).view_name, view_name)

    def test_upload_timeseries(self):
        view_name = "upload_timeseries"

        for language_code, _ in settings.LANGUAGES:
            with translation.override(language_code):
                url = f"/{language_code}/api/upload_timeseries/"
                self.assertEqual(reverse(view_name), url)
                self.assertEqual(resolve(url).view_name, view_name)

    def test_delete_timeseries(self):
        view_name = "delete_timeseries"

        for language_code, _ in settings.LANGUAGES:
            with translation.override(language_code):
                url = f"/{language_code}/api/delete_timeseries/"
                self.assertEqual(reverse(view_name), url)
                self.assertEqual(resolve(url).view_name, view_name)


class APIRunURLTestCase(TestCase):
    def test_build(self):
        view_name = "build"

        for language_code, _ in settings.LANGUAGES:
            with translation.override(language_code):
                url = f"/{language_code}/api/build/"
                self.assertEqual(reverse(view_name), url)
                self.assertEqual(resolve(url).view_name, view_name)

    def test_optimize(self):
        view_name = "optimize"

        for language_code, _ in settings.LANGUAGES:
            with translation.override(language_code):
                url = f"/{language_code}/api/optimize/"
                self.assertEqual(reverse(view_name), url)
                self.assertEqual(resolve(url).view_name, view_name)

    def test_delete_run(self):
        view_name = "delete_run"

        for language_code, _ in settings.LANGUAGES:
            with translation.override(language_code):
                url = f"/{language_code}/api/delete_run/"
                self.assertEqual(reverse(view_name), url)
                self.assertEqual(resolve(url).view_name, view_name)

    def test_update_run_description(self):
        view_name = "update_run_description"

        for language_code, _ in settings.LANGUAGES:
            with translation.override(language_code):
                url = f"/{language_code}/api/update_run_description/"
                self.assertEqual(reverse(view_name), url)
                self.assertEqual(resolve(url).view_name, view_name)

    def test_download(self):
        view_name = "download"

        for language_code, _ in settings.LANGUAGES:
            with translation.override(language_code):
                url = f"/{language_code}/api/download/"
                self.assertEqual(reverse(view_name), url)
                self.assertEqual(resolve(url).view_name, view_name)
