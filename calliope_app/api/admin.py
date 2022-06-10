from django.contrib import admin

from api.models.engage import Help_Guide
from api.models.calliope import Abstract_Tech, Abstract_Tech_Param, \
    Parameter, Run_Parameter
from api.models.configuration import Model, Model_User, Model_Comment, \
    Location, Technology, Tech_Param, Model_Favorite, User_File, \
    Loc_Tech, Loc_Tech_Param, Timeseries_Meta, Scenario, \
    Scenario_Loc_Tech, Scenario_Param
from api.models.outputs import Run
from api.models.engage import User_Profile, ComputeEnvironment


class ComputeEnvironmentAdmin(admin.ModelAdmin):
    filter_horizontal = ("users",)
    list_display = ['id',  'name', 'full_name', 'is_default', 'ncpu', 'memory', 'type', '_users']

    @staticmethod
    def _users(instance):
        """Return the number of users that can use the environment"""
        return instance.users.count()


class User_Profile_Admin(admin.ModelAdmin):
    list_display = ['id', 'user', 'organization', 'timezone', 'activation_uuid']


class Help_Guide_Admin(admin.ModelAdmin):
    # fields = []
    list_display = ['key', 'safe_html']


class Parameter_Admin(admin.ModelAdmin):
    # fields = []
    list_display = ['id', 'root', 'category', 'name', 'pretty_name',
                    'description', 'timeseries_enabled', 'units', 'choices',
                    'is_systemwide', 'is_essential', 'is_carrier']


class Abstract_Tech_Admin(admin.ModelAdmin):
    list_display = ['id', 'name', 'pretty_name', 'image',
                    'description', 'icon']


class Abstract_Tech_Param_Admin(admin.ModelAdmin):
    list_display = ['id', 'abstract_tech', 'parameter', 'default_value']


class Model_Admin(admin.ModelAdmin):
    list_display = ['id', 'name', 'snapshot_version', 'snapshot_base', 'uuid',
                    'public', 'is_uploading', 'created', 'updated']


class Model_User_Admin(admin.ModelAdmin):
    list_filter = ['model']
    list_display = ['id', 'model', 'user', 'can_edit',
                    'last_access', 'notifications']


class Model_Comment_Admin(admin.ModelAdmin):
    list_filter = ['model']
    list_display = ['id', 'model', 'user', 'type', 'comment', 'created']


class Model_Favorite_Admin(admin.ModelAdmin):
    list_filter = ['model']
    list_display = ['id', 'model', 'parameter']


class User_File_Admin(admin.ModelAdmin):
    list_filter = ['model']
    list_display = ['id', 'filename', 'description', 'model', 'created']


class Run_Parameter_Admin(admin.ModelAdmin):
    list_display = ['id', 'root', 'name', 'pretty_name', 'description',
                    'user_visibility', 'can_evolve',
                    'default_value', 'choices']


class Location_Admin(admin.ModelAdmin):
    list_filter = ['model']
    list_display = ['id', 'pretty_name', 'name', 'latitude', 'longitude',
                    'available_area', 'model', 'created', 'updated']


class Technology_Admin(admin.ModelAdmin):
    list_filter = ['model']
    list_display = ['id', 'pretty_name', 'abstract_tech', 'name', 'tag',
                    'pretty_tag', 'model', 'created', 'updated']


class Tech_Param_Admin(admin.ModelAdmin):
    list_filter = ['model']
    list_display = ['id', 'technology', 'year', 'parameter', 'value',
                    'raw_value', 'timeseries', 'timeseries_meta', 'model',
                    'created', 'updated']


class Loc_Tech_Admin(admin.ModelAdmin):
    list_filter = ['model']
    list_display = ['id', 'location_1', 'location_2', 'technology',
                    'model', 'created', 'updated']


class Loc_Tech_Param_Admin(admin.ModelAdmin):
    list_filter = ['model']
    list_display = ['id', 'loc_tech', 'year', 'parameter', 'value',
                    'raw_value', 'timeseries', 'timeseries_meta', 'model',
                    'created', 'updated']


class Timeseries_Meta_Admin(admin.ModelAdmin):
    list_filter = ['model']
    list_display = ['id', 'name', 'model', 'file_uuid', 'created',
                    'start_date', 'end_date',
                    'original_filename', 'original_timestamp_col',
                    'original_value_col', 'is_uploading', 'failure',
                    'message', 'upload_task']


class Scenario_Admin(admin.ModelAdmin):
    list_filter = ['model']
    list_display = ['id', 'name', 'model', 'created', 'updated']


class Scenario_Loc_Tech_Admin(admin.ModelAdmin):
    list_filter = ['model']
    list_display = ['id', 'scenario', 'loc_tech', 'model', 'created']


class Scenario_Param_Admin(admin.ModelAdmin):
    list_filter = ['model']
    list_display = ['id', 'scenario', 'run_parameter', 'year', 'value',
                    'model', 'created', 'updated']


class Run_Admin(admin.ModelAdmin):
    list_filter = ['model', 'calliope_066_upgraded', 'status','cluster','manual']
    list_display = ['id', 'scenario', 'year', 'subset_time', 'status',
                    'message', 'description', 'created', 'updated',
                    'inputs_path', 'logs_path', 'outputs_path', 'outputs_key',
                    'plots_path', 'model', 'build_task', 'run_task',
                    'deprecated', 'published','cluster','manual',
                    'calliope_066_upgraded', 'calliope_066_errors']


admin.site.register(Help_Guide, Help_Guide_Admin)
admin.site.register(Parameter, Parameter_Admin)
admin.site.register(Abstract_Tech, Abstract_Tech_Admin)
admin.site.register(Abstract_Tech_Param, Abstract_Tech_Param_Admin)
admin.site.register(Run_Parameter, Run_Parameter_Admin)
admin.site.register(Model, Model_Admin)
admin.site.register(Model_User, Model_User_Admin)
admin.site.register(User_Profile, User_Profile_Admin)
admin.site.register(Model_Comment, Model_Comment_Admin)
admin.site.register(Model_Favorite, Model_Favorite_Admin)
admin.site.register(User_File, User_File_Admin)
admin.site.register(Location, Location_Admin)
admin.site.register(Technology, Technology_Admin)
admin.site.register(Tech_Param, Tech_Param_Admin)
admin.site.register(Loc_Tech, Loc_Tech_Admin)
admin.site.register(Loc_Tech_Param, Loc_Tech_Param_Admin)
admin.site.register(Timeseries_Meta, Timeseries_Meta_Admin)
admin.site.register(Scenario, Scenario_Admin)
admin.site.register(Scenario_Loc_Tech, Scenario_Loc_Tech_Admin)
admin.site.register(Scenario_Param, Scenario_Param_Admin)
admin.site.register(Run, Run_Admin)
admin.site.register(ComputeEnvironment, ComputeEnvironmentAdmin)
