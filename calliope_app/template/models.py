from django.db import models
from api.models.calliope import Abstract_Tech, Parameter
from api.models.configuration import Location, Model, Timeseries_Meta
from django.contrib.postgres.fields import ArrayField

from api.models.utils import EngageManager

# Create your models here.
class Template_Types(models.Model):
    class Meta:
        db_table = "template_types"
        verbose_name_plural = "[Admin] Template Types"

    name = models.CharField(max_length=200)
    pretty_name = models.CharField(max_length=200)
    description = models.TextField(blank=True, null=True)
    category = models.CharField(max_length=200, blank=True, null=True)
    choices = ArrayField(models.CharField(max_length=10), blank=True, null=True)

    def __str__(self):
        return '%s' % (self.pretty_name)


class Template_Type_Variables(models.Model):
    class Meta:
        db_table = "template_type_variables"
        verbose_name_plural = "[Admin] Template Type Variables"

    name = models.CharField(max_length=200)
    units = models.CharField(max_length=200)
    default_value = models.CharField(max_length=200)
    description = models.TextField(blank=True, null=True)
    template_type = models.ForeignKey(Template_Types, on_delete=models.CASCADE)
    timeseries_enabled = models.BooleanField(blank=True, null=True)

    def __str__(self):
        return '%s' % (self.name)

class Template_Type_Locs(models.Model):
    class Meta:
        db_table = "template_type_locs"
        verbose_name_plural = "[Admin] Template Type Locs"

    name = models.CharField(max_length=200)
    latitude_offset = models.FloatField()
    longitude_offset = models.FloatField()
    template_type = models.ForeignKey(Template_Types, on_delete=models.CASCADE)

    def __str__(self):
        return '%s' % (self.name)

class Template_Type_Techs(models.Model):
    class Meta:
        db_table = "template_type_techs"
        verbose_name_plural = "[Admin] Template Type Techs"

    name = models.CharField(max_length=200)
    abstract_tech = models.ForeignKey(Abstract_Tech, on_delete=models.CASCADE)
    #Should we model carrier in and out similar to technologies?
    carrier_in = models.CharField(max_length=200)
    carrier_out = models.CharField(max_length=200)
    #color = models.CharField(max_length=200) looks like technologies is doing something fancy with this
    template_type = models.ForeignKey(Template_Types, on_delete=models.CASCADE)

    # @property
    # def carrier_in(self):
    #     """ Lookup the input carrier from the technology's parameters """
    #     p = Tech_Param.objects.filter(technology=self,
    #                                   parameter__name__in=Parameter.C_INS
    #                                   ).order_by('value')
    #     return ','.join(list(p.values_list('value', flat=True)))

    def __str__(self):
        return '%s' % (self.name)

class Template_Type_Loc_Techs(models.Model):
    class Meta:
        db_table = "template_type_loc_techs"
        verbose_name_plural = "[Admin] Template Type Loc Techs"
    name = models.CharField(max_length=200)
    template_type = models.ForeignKey(Template_Types, on_delete=models.CASCADE)
    template_loc = models.ForeignKey(Template_Type_Locs, on_delete=models.CASCADE)
    template_tech = models.ForeignKey(Template_Type_Techs, on_delete=models.CASCADE)

    def __str__(self):
        return '%s' % (self.name)

class Template_Type_Parameters(models.Model):
    class Meta:
        db_table = "template_type_parameters"
        verbose_name_plural = "[Admin] Template Type Parameters"

    template_loc_tech = models.ForeignKey(Template_Type_Loc_Techs, on_delete=models.CASCADE)
    parameter = models.ForeignKey(Parameter, on_delete=models.CASCADE)
    equation = models.CharField(max_length=200)

    def __str__(self):
        return '%s' % (self.equation)

class Templates(models.Model):
    class Meta:
        db_table = "templates"
        verbose_name_plural = "Templates"
        ordering = ['name']
    objects = EngageManager()
    #????????
    objects_all = models.Manager()

    name = models.CharField(max_length=200)
    #look into template type
    template_type = models.ForeignKey(Template_Types, on_delete=models.CASCADE)
    model = models.ForeignKey(Model, on_delete=models.CASCADE)
    location = models.ForeignKey(Location,
                            on_delete=models.CASCADE,
                            related_name="location",
                            blank=True, null=True)
    created = models.DateTimeField(auto_now_add=True, null=True)
    updated = models.DateTimeField(auto_now=True, null=True)
    deleted = models.DateTimeField(default=None, editable=False, null=True)

    def __str__(self):
        return '%s' % (self.name)

class Template_Variables(models.Model):
    class Meta:
        db_table = "template_variables"
        verbose_name_plural = "Template Variables"
    objects = EngageManager()
    objects_all = models.Manager()

    #look into template type
    template = models.ForeignKey(Templates, on_delete=models.CASCADE)
    template_type_variable = models.ForeignKey(Template_Type_Variables, on_delete=models.CASCADE)
    value = models.CharField(max_length=200)
    timeseries = models.BooleanField(default=False)
    timeseries_meta = models.ForeignKey(Timeseries_Meta,
                                        on_delete=models.CASCADE,
                                        blank=True, null=True)
    created = models.DateTimeField(auto_now_add=True, null=True)
    updated = models.DateTimeField(auto_now=True, null=True)
    deleted = models.DateTimeField(default=None, editable=False, null=True)

    def __str__(self):
        return '%s' % (self.template)

