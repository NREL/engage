from django.contrib import admin
from template.models import Template, Template_Variable, Template_Type, Template_Type_Variable, Template_Type_Loc, Template_Type_Tech, Template_Type_Loc_Tech, Template_Type_Parameter

# Register your models here.
class Templates_View(admin.ModelAdmin):
    list_filter = ['id', 'model']
    list_display = ['id', 'name', 'template_type', 'model', 'location', 'created', 'updated']
class Template_Variable_View(admin.ModelAdmin):
    list_filter = ['id', 'template', 'template_type_variable']
    list_display = ['id', 'template', 'template_type_variable', 'value', 'raw_value', 'timeseries', 'timeseries_meta', 'updated']
class Template_Type_Admin(admin.ModelAdmin):
    list_filter = ['id', 'name']
    list_display = ['id', 'name', 'pretty_name', 'description']
class Template_Type_Variable_Admin(admin.ModelAdmin):
    list_filter = ['id']
    list_display = ['id', 'name', 'pretty_name', 'template_type', 'units', 'default_value', 'category', 'choices', 'description', 'timeseries_enabled']
class Template_Type_Loc_Admin(admin.ModelAdmin):
    list_filter = ['id']
    list_display = ['id', 'name', 'template_type', 'latitude_offset', 'longitude_offset']
class Template_Type_Tech_Admin(admin.ModelAdmin):
    list_filter = ['id']
    list_display = ['id', 'name', 'template_type', 'abstract_tech', 'carrier_in', 'carrier_out']
class Template_Type_Loc_Tech_Admin(admin.ModelAdmin):
    list_filter = ['id']
    list_display = ['id', 'template_type', 'template_loc_1', 'template_loc_2' , 'template_tech']
class Template_Type_Parameter_Admin(admin.ModelAdmin):
    list_filter = ['id']
    list_display = ['id', 'template_loc_tech', 'parameter', 'equation']

admin.site.register(Template, Templates_View)
admin.site.register(Template_Variable, Template_Variable_View)
admin.site.register(Template_Type, Template_Type_Admin)
admin.site.register(Template_Type_Variable, Template_Type_Variable_Admin)
admin.site.register(Template_Type_Loc, Template_Type_Loc_Admin)
admin.site.register(Template_Type_Tech, Template_Type_Tech_Admin)
admin.site.register(Template_Type_Loc_Tech, Template_Type_Loc_Tech_Admin)
admin.site.register(Template_Type_Parameter, Template_Type_Parameter_Admin)