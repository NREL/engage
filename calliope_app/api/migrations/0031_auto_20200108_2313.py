# Generated by Django 2.1.4 on 2020-01-08 23:13

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0030_user_profile_activation_uuid'),
    ]

    operations = [
        migrations.AddField(
            model_name='parameter',
            name='is_expansion',
            field=models.BooleanField(null=True),
        ),
        migrations.AddField(
            model_name='parameter',
            name='is_linear',
            field=models.BooleanField(null=True),
        ),
        migrations.AddField(
            model_name='technology',
            name='is_expansion',
            field=models.BooleanField(null=True),
        ),
        migrations.AddField(
            model_name='technology',
            name='is_linear',
            field=models.BooleanField(null=True),
        ),
    ]
