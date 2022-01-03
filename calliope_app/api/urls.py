from django.urls import path

from .views import configuration as configuration_views
from .views import engage as engage_views
from .views import outputs as outputs_views

urlpatterns = [
    # Upgrades
    path('upgrade_066/',
         engage_views.apply_upgrade_066,
         name='upgrade_066'),

    # Models
    path('add_model/',
         configuration_views.add_model,
         name='add_model'),
    path('remove_model/',
         configuration_views.remove_model,
         name='remove_model'),
    path('duplicate_model/',
         configuration_views.duplicate_model,
         name='duplicate_model'),
    path('add_collaborator/',
         configuration_views.add_collaborator,
         name='add_collaborator'),
    path('add_model_comment/',
         configuration_views.add_model_comment,
         name='add_model_comment'),

    # Locations
    path('update_location/',
         configuration_views.update_location,
         name='update_location'),
    path('delete_location/',
         configuration_views.delete_location,
         name='delete_location'),

    # Parameters
    path('convert_to_timeseries/',
         configuration_views.convert_to_timeseries,
         name='convert_to_timeseries'),
    path('update_favorite/',
         configuration_views.update_favorite,
         name='update_favorite'),

    # Technologies
    path('add_technology/',
         configuration_views.add_technology,
         name='add_technology'),
    path('delete_technology/',
         configuration_views.delete_technology,
         name='delete_technology'),
    path('update_tech_params/',
         configuration_views.update_tech_params,
         name='update_tech_params'),

    # Location Technologies
    path('add_loc_tech/',
         configuration_views.add_loc_tech,
         name='add_loc_tech'),
    path('delete_loc_tech/',
         configuration_views.delete_loc_tech,
         name='delete_loc_tech'),
    path('update_loc_tech_params/',
         configuration_views.update_loc_tech_params,
         name='update_loc_tech_params'),

    # Scenarios
    path('add_scenario/',
         configuration_views.add_scenario,
         name='add_scenario'),
    path('toggle_scenario_loc_tech/',
         configuration_views.toggle_scenario_loc_tech,
         name='toggle_scenario_loc_tech'),
    path('update_scenario_params/',
         configuration_views.update_scenario_params,
         name='update_scenario_params'),
    path('delete_scenario/',
         configuration_views.delete_scenario,
         name='delete_scenario'),

    # Files
    path('upload_file/',
         configuration_views.upload_file,
         name='upload_file'),
    path('delete_file/',
         configuration_views.delete_file,
         name='delete_file'),
    path('import_timeseries/',
         configuration_views.import_timeseries,
         name='import_timeseries'),
    path('upload_timeseries/',
         configuration_views.upload_timeseries,
         name='upload_timeseries'),
    path('delete_timeseries/',
         configuration_views.delete_timeseries,
         name='delete_timeseries'),
    path('wtk_timeseries/',
         configuration_views.wtk_timeseries,
         name='wtk_timeseries'),

    # Runs
    path('build/',
         outputs_views.build,
         name='build'),
    path('optimize/',
         outputs_views.optimize,
         name='optimize'),
    path('delete_run/',
         outputs_views.delete_run,
         name='delete_run'),
    path('publish_run/',
         outputs_views.publish_run,
         name='publish_run'),
    path('update_run_description/',
         outputs_views.update_run_description,
         name='update_run_description'),
    path('download/',
         outputs_views.download,
         name='download'),
    path('upload_outputs/',
         outputs_views.upload_outputs,
         name='upload_outputs')]
