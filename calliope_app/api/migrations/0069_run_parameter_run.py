# Generated by Django 3.2.25 on 2024-05-07 16:19

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0068_scenario_param_tab'),
    ]

    operations = [
        migrations.AddField(
            model_name='run_parameter',
            name='run',
            field=models.JSONField(blank=True, null=True),
        ),
    ]
