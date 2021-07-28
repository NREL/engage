from django.db import models
from django.contrib.postgres.fields import ArrayField


class Parameter(models.Model):
    class Meta:
        db_table = "parameter"
        verbose_name_plural = "[Admin] Parameters"

    C_INS = ['carrier', 'carrier_in', 'carrier_in_2', 'carrier_in_3']
    C_OUTS = ['carrier', 'carrier_out', 'carrier_out_2', 'carrier_out_3']

    root = models.CharField(max_length=200)
    category = models.CharField(max_length=200)
    name = models.CharField(max_length=200)
    pretty_name = models.CharField(max_length=200)
    description = models.TextField(blank=True, null=True)
    timeseries_enabled = models.BooleanField()
    units = models.CharField(max_length=200)
    choices = ArrayField(models.CharField(max_length=20, blank=True))
    is_systemwide = models.BooleanField(default=False)
    is_essential = models.BooleanField(default=False)
    is_carrier = models.BooleanField(default=False)

    def __str__(self):
        return '%s' % (self.pretty_name)


class Abstract_Tech(models.Model):
    class Meta:
        db_table = "abstract_tech"
        verbose_name_plural = "[Admin] Abstract Technologies"
        ordering = ['id']

    name = models.CharField(max_length=200)
    pretty_name = models.CharField(max_length=200)
    image = models.CharField(max_length=200)
    description = models.TextField(blank=True, null=True)
    icon = models.CharField(max_length=200, blank=True, null=True)

    def __str__(self):
        return '%s (%s)' % (self.pretty_name, self.name)


class Abstract_Tech_Param(models.Model):
    class Meta:
        db_table = "abstract_tech_param"
        verbose_name_plural = "[Admin] Abstract Technology Parameters"

    abstract_tech = models.ForeignKey(Abstract_Tech, on_delete=models.CASCADE)
    parameter = models.ForeignKey(Parameter, on_delete=models.CASCADE)
    default_value = models.CharField(max_length=200)


class Run_Parameter(models.Model):
    class Meta:
        db_table = "run_parameter"
        verbose_name_plural = "[Admin] Run Parameters"

    root = models.CharField(max_length=200)
    name = models.CharField(max_length=200)
    pretty_name = models.CharField(max_length=200)
    description = models.TextField(blank=True, null=True)
    user_visibility = models.BooleanField()
    can_evolve = models.BooleanField(default=False)
    default_value = models.CharField(max_length=200)
    choices = ArrayField(models.CharField(max_length=10, blank=True))

    def __str__(self):
        return '%s (%s)' % (self.pretty_name, self.name)
