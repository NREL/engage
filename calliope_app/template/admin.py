from django.contrib import admin
from template.models import Template_Types, Template_Type_Variables, Template_Type_Locs, Template_Type_Techs, Template_Type_Loc_Techs, Template_Type_Parameters

# Register your models here.
class Template_Types_Admin(admin.ModelAdmin):
    # Add a different filter name?
    #list_filter = ['model']
    list_display = ['id', 'name', 'pretty_name', 'description']
class Template_Type_Variables_Admin(admin.ModelAdmin):
    # Add a different filter name?
    #list_filter = ['model']
    list_display = ['id', 'template', 'name', 'units', 'default_value', 'description']
class Template_Type_Locs_Admin(admin.ModelAdmin):
    # Add a different filter name?
    #list_filter = ['model']
    list_display = ['id', 'template', 'name', 'latitude_offset', 'longitude_offset', 'primary_location']
class Template_Type_Techs_Admin(admin.ModelAdmin):
    # Add a different filter name?
    #list_filter = ['model']
    list_display = ['id', 'template', 'name', 'abstract_tech', 'carrier_in', 'carrier_out']
class Template_Type_Loc_Techs_Admin(admin.ModelAdmin):
    # Add a different filter name?
    #list_filter = ['model']
    #Do loc_techs need a name too?
    list_display = ['id', 'template', 'template_loc', 'template_tech']
class Template_Type_Parameters_Admin(admin.ModelAdmin):
    # Add a different filter name?
    #list_filter = ['model']
    list_display = ['id', 'template_tech', 'parameter', 'equation']

admin.site.register(Template_Types, Template_Types_Admin)
admin.site.register(Template_Type_Variables, Template_Type_Variables_Admin)
admin.site.register(Template_Type_Locs, Template_Type_Locs_Admin)
admin.site.register(Template_Type_Techs, Template_Type_Techs_Admin)
admin.site.register(Template_Type_Loc_Techs, Template_Type_Loc_Techs_Admin)
admin.site.register(Template_Type_Parameters, Template_Type_Parameters_Admin)