# Generated by Django 2.1.4 on 2019-09-04 00:24

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0020_timeseries_meta_is_uploading'),
    ]

    operations = [
        migrations.AddField(
            model_name='model_user',
            name='last_access',
            field=models.DateTimeField(auto_now=True, null=True),
        ),
    ]
