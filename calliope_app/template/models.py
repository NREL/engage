from django.db import models
from api.models.calliope import Abstract_Tech, Parameter
from api.models.configuration import Location

# Create your models here.
class Template(models.Model):
    class Meta:
        db_table = "template"
        verbose_name_plural = "[Admin] Template"

    name = models.CharField(max_length=200)
    pretty_name = models.CharField(max_length=200)
    description = models.TextField(blank=True, null=True)

    def __str__(self):
        return '%s' % (self.pretty_name)


class Template_Option_Param(models.Model):
    class Meta:
        db_table = "template_option_param"
        verbose_name_plural = "[Admin] Template Option Param"

    name = models.CharField(max_length=200)
    units = models.CharField(max_length=200)
    default_value = models.CharField(max_length=200)
    description = models.TextField(blank=True, null=True)
    template = models.ForeignKey(template, on_delete=models.CASCADE)

    def __str__(self):
        return '%s' % (self.pretty_name)

class Template_Loc_Structure(models.Model):
    class Meta:
        db_table = "template_loc_structure"
        verbose_name_plural = "[Admin] Template Loc Structure"

    name = models.CharField(max_length=200)
    latitude_offset = models.FloatField()
    longitude_offset = models.FloatField()
    template = models.ForeignKey(template, on_delete=models.CASCADE)
    primary_location = models.ForeignKey(Location,
                                on_delete=models.CASCADE,
                                related_name="primary_location",
                                blank=True, null=True)

    def __str__(self):
        return '%s' % (self.pretty_name)

class Template_Tech_Structure(models.Model):
    class Meta:
        db_table = "template_tech_structure"
        verbose_name_plural = "[Admin] Template Tech Structure"

    name = models.CharField(max_length=200)
    abstract_tech = models.ForeignKey(Abstract_Tech, on_delete=models.CASCADE)
    #Should we model carrier in and out similar to technologies?
    carrier_in = models.CharField(max_length=200)
    carrier_out = models.CharField(max_length=200)
    #color = models.CharField(max_length=200) looks like technologies is doing something fancy with this
    template = models.ForeignKey(template, on_delete=models.CASCADE)

    # @property
    # def carrier_in(self):
    #     """ Lookup the input carrier from the technology's parameters """
    #     p = Tech_Param.objects.filter(technology=self,
    #                                   parameter__name__in=Parameter.C_INS
    #                                   ).order_by('value')
    #     return ','.join(list(p.values_list('value', flat=True)))

    def __str__(self):
        return '%s' % (self.pretty_name)

class Template_Loc_Tech_Structure(models.Model):
    class Meta:
        db_table = "template_locs_tech_structure"
        verbose_name_plural = "[Admin] Template Loc Tech Structure"

    template = models.ForeignKey(template, on_delete=models.CASCADE)
    template_loc = models.ForeignKey(template_loc_structure, on_delete=models.CASCADE)
    template_tech = models.ForeignKey(template_tech_structure, on_delete=models.CASCADE)

    def __str__(self):
        return '%s' % (self.pretty_name)

class Template_Parameter(models.Model):
    class Meta:
        db_table = "template_parameter"
        verbose_name_plural = "[Admin] Template Parameter"

    template_tech = models.ForeignKey(template_locs_tech_structure, on_delete=models.CASCADE)
    parameter = models.ForeignKey(Parameter, on_delete=models.CASCADE)
    equation = models.CharField(max_length=200)

    def __str__(self):
        return '%s' % (self.pretty_name)