# Generated by Django 3.2.15 on 2023-04-22 04:06

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('template', '0002_auto_20230421_1635'),
    ]

    operations = [
        migrations.AddField(
            model_name='template_type_variable',
            name='max',
            field=models.CharField(blank=True, max_length=200, null=True),
        ),
        migrations.AddField(
            model_name='template_type_variable',
            name='min',
            field=models.CharField(blank=True, max_length=200, null=True),
        ),
    ]