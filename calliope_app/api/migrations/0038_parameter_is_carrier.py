# Generated by Django 2.1.4 on 2020-02-09 21:59

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0037_auto_20200209_2146'),
    ]

    operations = [
        migrations.AddField(
            model_name='parameter',
            name='is_carrier',
            field=models.BooleanField(default=False),
        ),
    ]
