# Generated by Django 2.1.4 on 2019-12-23 06:14

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0028_auto_20191222_1612'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='scenario_loc_tech',
            options={'ordering': ['loc_tech__technology__name'], 'verbose_name_plural': '[4] Scenario Location Technologies'},
        ),
        migrations.AddField(
            model_name='timeseries_meta',
            name='failure',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='timeseries_meta',
            name='message',
            field=models.TextField(blank=True, null=True),
        ),
    ]
