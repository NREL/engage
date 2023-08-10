from django.db import models
from api.models.calliope import Abstract_Tech, Parameter
from api.models.configuration import Location, Model, Timeseries_Meta, Technology, Technology, Abstract_Tech, Loc_Tech
from django.contrib.postgres.fields import ArrayField
from django.db.models.signals import pre_delete 
from django.dispatch import receiver
from django.db.models.signals import post_delete

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
    units = models.CharField(max_length=200, blank=True, null=True)
    default_value = models.CharField(max_length=200, blank=True, null=True)
    min = models.CharField(max_length=200, blank=True, null=True)
    max = models.CharField(max_length=200, blank=True, null=True)
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
    description = models.CharField(max_length=200, blank=True, null=True)
    template_type = models.ForeignKey(Template_Type, on_delete=models.CASCADE)
    abstract_tech = models.ForeignKey(Abstract_Tech, on_delete=models.CASCADE)
    version_tag = models.CharField(max_length=200, blank=True, null=True)
    energy_carrier = models.CharField(max_length=200, blank=True, null=True)
    carrier_in = models.CharField(max_length=200, blank=True, null=True)
    carrier_out = models.CharField(max_length=200, blank=True, null=True)
    carrier_in_2 = models.CharField(max_length=200, blank=True, null=True)
    carrier_out_2 = models.CharField(max_length=200, blank=True, null=True)
    carrier_in_3 = models.CharField(max_length=200, blank=True, null=True)
    carrier_out_3 = models.CharField(max_length=200, blank=True, null=True)
    carrier_ratios = models.CharField(max_length=200, blank=True, null=True)
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
    
class Template_Type_Carrier(models.Model):
    class Meta:
        db_table = "template_type_carrier"
        verbose_name_plural = "[Admin] Template Type Carriers"
        ordering = ['name']

    template_type = models.ForeignKey(Template_Type, on_delete=models.CASCADE)
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True, null=True)
    rate_unit = models.CharField(max_length=20)
    quantity_unit = models.CharField(max_length=20)

    def __str__(self):
        return '%s' % (self.name)

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

@receiver(post_delete, sender=Template)
def signal_function_name(sender, instance, using, **kwargs):
    if sender == Template:
        template_id = instance.id
        print ("Cleaning up assoicatted records for " + str(template_id))

        # Loop through techs 
        technologies = Technology.objects.filter(template_type_id=instance.template_type_id, model_id=instance.model)

        for tech in technologies:
            # Delete if there are no other nodes outside of the template are using this tech
            loc_techs = Loc_Tech.objects.filter(technology=tech)
            uniqueToTemplate = True
            for loc_tech in loc_techs:
                if loc_tech.template_id != int(template_id):
                    print("tech not unique to template loc_tech.template_id: " + str(loc_tech.template_id) + " template_id: " + str(template_id))
                    uniqueToTemplate = False
                    break
            
            if uniqueToTemplate:
                Technology.objects.filter(id=tech.id).delete()

        # Delete any remaining nodes, locations and the template itself
        Loc_Tech.objects.filter(template_id=template_id).delete()
        Location.objects.filter(template_id=template_id).delete()