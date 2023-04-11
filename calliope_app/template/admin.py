from django.contrib import admin
from template.models import Templates, Template_Variables, Template_Types, Template_Type_Variables, Template_Type_Locs, Template_Type_Techs, Template_Type_Loc_Techs, Template_Type_Parameters

# Register your models here.
class Templates_View(admin.ModelAdmin):
    list_filter = ['id', 'model']
    list_display = ['id', 'name', 'template_type', 'model', 'location', 'created', 'updated']
class Template_Variables_View(admin.ModelAdmin):
    list_filter = ['id', 'template', 'template_type_variable']
    list_display = ['id', 'template', 'template_type_variable', 'value', 'timeseries', 'timeseries_meta', 'updated']
class Template_Types_Admin(admin.ModelAdmin):
    list_filter = ['id', 'name']
    list_display = ['id', 'name', 'pretty_name', 'description']
class Template_Type_Variables_Admin(admin.ModelAdmin):
    list_filter = ['id']
    list_display = ['id', 'name', 'pretty_name', 'template_type', 'units', 'default_value', 'category', 'choices', 'description', 'timeseries_enabled']
class Template_Type_Locs_Admin(admin.ModelAdmin):
    list_filter = ['id']
    list_display = ['id', 'name', 'template_type', 'latitude_offset', 'longitude_offset']
class Template_Type_Techs_Admin(admin.ModelAdmin):
    list_filter = ['id']
    list_display = ['id', 'name', 'template_type', 'abstract_tech', 'carrier_in', 'carrier_out']
class Template_Type_Loc_Techs_Admin(admin.ModelAdmin):
    list_filter = ['id']
    list_display = ['id', 'template_type', 'template_loc_1', 'template_loc_2' , 'template_tech']
class Template_Type_Parameters_Admin(admin.ModelAdmin):
    list_filter = ['id']
    list_display = ['id', 'template_loc_tech', 'parameter', 'equation']

admin.site.register(Templates, Templates_View)
admin.site.register(Template_Variables, Template_Variables_View)
admin.site.register(Template_Types, Template_Types_Admin)
admin.site.register(Template_Type_Variables, Template_Type_Variables_Admin)
admin.site.register(Template_Type_Locs, Template_Type_Locs_Admin)
admin.site.register(Template_Type_Techs, Template_Type_Techs_Admin)
admin.site.register(Template_Type_Loc_Techs, Template_Type_Loc_Techs_Admin)
admin.site.register(Template_Type_Parameters, Template_Type_Parameters_Admin)