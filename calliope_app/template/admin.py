from django.contrib import admin
from template.models import Template, Template_Option_Param, Template_Loc_Structure, Template_Tech_Structure, Template_Loc_Tech_Structure, Template_Parameter

# Register your models here.
class Template_Admin(admin.ModelAdmin):
    # Add a different filter name?
    list_filter = ['model']
    list_display = ['id', 'name', 'pretty_name', 'description']
class Template_Option_Param_Admin(admin.ModelAdmin):
    # Add a different filter name?
    list_filter = ['model']
    list_display = ['id', 'template', 'name', 'units', 'default_value', 'description']
class Template_Loc_Structure_Admin(admin.ModelAdmin):
    # Add a different filter name?
    list_filter = ['model']
    list_display = ['id', 'template', 'name', 'latitude_offset', 'longitude_offset', 'primary_location']
class Template_Tech_Structure_Admin(admin.ModelAdmin):
    # Add a different filter name?
    list_filter = ['model']
    list_display = ['id', 'template', 'name', 'abstract_tech', 'carrier_in', 'carrier_out']
class Template_Loc_Tech_Structure_Admin(admin.ModelAdmin):
    # Add a different filter name?
    list_filter = ['model']
    #Do loc_techs need a name too?
    list_display = ['id', 'template', 'template_loc', 'template_tech']
class Template_Parameter(admin.ModelAdmin):
    # Add a different filter name?
    list_filter = ['model']
    list_display = ['id', 'template_tech', 'parameter', 'equation']

admin.site.register(Template, Template_Admin)
#admin.site.register(Template_Option_Param, Template_Option_Param_Admin)
#admin.site.register(Template_Loc_Structure, Template_Loc_Structure_Admin)
#admin.site.register(Template_Tech_Structure, Template_Tech_Structure_Admin)
#admin.site.register(Template_Loc_Tech_Structure, Template_Loc_Tech_Structure_Admin)
#admin.site.register(Template_Parameter, Template_Parameter_Admin)