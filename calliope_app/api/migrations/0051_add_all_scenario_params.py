# Generated by Rob Spencer on 2021-05-06
from django.db import migrations


def forward(apps, schema_editor):
    scenarios = apps.get_model('api', 'Scenario').objects.all()
    parameters = apps.get_model('api', 'Run_Parameter').objects.all()
    Scenario_Param = apps.get_model('api', 'Scenario_Param')

    for scenario in scenarios:
        model = scenario.model
        existing_param_ids = list(Scenario_Param.objects.filter(
            scenario=scenario).values_list('run_parameter_id', flat=True))
        for param in parameters:
            if param.id in existing_param_ids:
                continue
            if param.name == "name":
                value = "{}: {}".format(model.name, scenario.name)
            else:
                value = param.default_value

            Scenario_Param.objects.create(
                scenario=scenario, run_parameter=param,
                value=value, model=model)


def reverse(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0050_auto_20210729_2028'),
    ]

    operations = [
        migrations.RunPython(forward, reverse),
    ]