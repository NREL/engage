from django.db import models
from api.models.calliope import Abstract_Tech, Parameter
from api.models.configuration import Location, Model, Timeseries_Meta
from django.contrib.postgres.fields import ArrayField
from django.db.models.signals import pre_delete 
from django.dispatch import receiver

from api.models.utils import EngageManager

# Create your models here.
class Template_Type(models.Model):
    class Meta:
        db_table = "template_types"
        verbose_name_plural = "[Admin] Template Types"

    name = models.CharField(max_length=200)
    pretty_name = models.CharField(max_length=200)
    description = models.TextField(blank=True, null=True)

    def __str__(self):
        return '%s' % (self.pretty_name)


class Template_Type_Variable(models.Model):
    class Meta:
        db_table = "template_type_variables"
        verbose_name_plural = "[Admin] Template Type Variables"

    name = models.CharField(max_length=200)
    pretty_name = models.CharField(max_length=200)
    template_type = models.ForeignKey(Template_Type, on_delete=models.CASCADE)
    units = models.CharField(max_length=200)
    default_value = models.CharField(max_length=200, blank=True, null=True)
    description = models.TextField(blank=True, null=True)
    timeseries_enabled = models.BooleanField(blank=True, null=True)
    category = models.CharField(max_length=200, blank=True, null=True)
    choices = ArrayField(models.CharField(max_length=10), blank=True, null=True)

    def __str__(self):
        return '%s' % (self.name)

class Template_Type_Loc(models.Model):
    class Meta:
        db_table = "template_type_locs"
        verbose_name_plural = "[Admin] Template Type Locs"

    name = models.CharField(max_length=200)
    template_type = models.ForeignKey(Template_Type, on_delete=models.CASCADE)
    latitude_offset = models.FloatField()
    longitude_offset = models.FloatField()

    def __str__(self):
        return '%s' % (self.name)

class Template_Type_Tech(models.Model):
    class Meta:
        db_table = "template_type_techs"
        verbose_name_plural = "[Admin] Template Type Techs"

    name = models.CharField(max_length=200)
    template_type = models.ForeignKey(Template_Type, on_delete=models.CASCADE)
    abstract_tech = models.ForeignKey(Abstract_Tech, on_delete=models.CASCADE)
    #Should we model carrier in and out similar to technologies?
    carrier_in = models.CharField(max_length=200)
    carrier_out = models.CharField(max_length=200, blank=True, null=True)
    #color = models.CharField(max_length=200) looks like technologies is doing something fancy with this

    # @property
    # def carrier_in(self):
    #     """ Lookup the input carrier from the technology's parameters """
    #     p = Tech_Param.objects.filter(technology=self,
    #                                   parameter__name__in=Parameter.C_INS
    #                                   ).order_by('value')
    #     return ','.join(list(p.values_list('value', flat=True)))

    def __str__(self):
        return '%s' % (self.name)

class Template_Type_Loc_Tech(models.Model):
    class Meta:
        db_table = "template_type_loc_techs"
        verbose_name_plural = "[Admin] Template Type Loc Techs"
    template_type = models.ForeignKey(Template_Type, on_delete=models.CASCADE)
    template_loc_1 = models.ForeignKey(Template_Type_Loc,
                                   on_delete=models.CASCADE,
                                   related_name="template_loc_1")
    template_loc_2 = models.ForeignKey(Template_Type_Loc,
                                   on_delete=models.CASCADE,
                                   related_name="template_loc_2",
                                   blank=True, null=True)
    template_tech = models.ForeignKey(Template_Type_Tech, on_delete=models.CASCADE)

    def __str__(self):
        if self.template_loc_2:
            return '%s[%s] at %s <-> %s' % (self.template_tech, self.template_tech.abstract_tech, self.template_loc_1, self.template_loc_2)
        else:
            return '%s[%s] at %s' % (self.template_tech, self.template_tech.abstract_tech, self.template_loc_1)

class Template_Type_Parameter(models.Model):
    class Meta:
        db_table = "template_type_parameters"
        verbose_name_plural = "[Admin] Template Type Parameters"

    template_loc_tech = models.ForeignKey(Template_Type_Loc_Tech, on_delete=models.CASCADE)
    parameter = models.ForeignKey(Parameter, on_delete=models.CASCADE)
    equation = models.CharField(max_length=200)

    def __str__(self):
        return '%s' % (self.equation)

class Template(models.Model):
    class Meta:
        db_table = "templates"
        verbose_name_plural = "Templates"
        ordering = ['name']
    objects = EngageManager()
    objects_all = models.Manager()

    name = models.CharField(max_length=200)
    template_type = models.ForeignKey(Template_Type, on_delete=models.CASCADE)
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

    @receiver(pre_delete)
    def delete_repo(sender, instance, **kwargs):
        print ("delete_repo " + str(instance))
        if sender == Template:
            #shutil.rmtree(instance.repo) import shutil
            print ("sender delete_repo " + str(instance))
    
    # @classmethod
    # def _delete(cls, template, data):
    #     print ("_delete " + data + template)


class Template_Variable(models.Model):
    class Meta:
        db_table = "template_variables"
        verbose_name_plural = "Template Variables"
    objects = EngageManager()
    objects_all = models.Manager()

    template = models.ForeignKey(Template, on_delete=models.CASCADE)
    template_type_variable = models.ForeignKey(Template_Type_Variable, on_delete=models.CASCADE)
    value = models.CharField(max_length=200)
    raw_value = models.CharField(max_length=200, blank=True, null=True)
    timeseries = models.BooleanField(default=False)
    timeseries_meta = models.ForeignKey(Timeseries_Meta,
                                        on_delete=models.CASCADE,
                                        blank=True, null=True)
    created = models.DateTimeField(auto_now_add=True, null=True)
    updated = models.DateTimeField(auto_now=True, null=True)
    deleted = models.DateTimeField(default=None, editable=False, null=True)

    def __str__(self):
        return '%s' % (self.template_type_variable)

