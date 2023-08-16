# Generated by Django 3.2.15 on 2023-05-20 03:03

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('template', '0004_template_type_tech_energy_carrier'),
    ]

    operations = [
        migrations.AddField(
            model_name='template_type_tech',
            name='description',
            field=models.CharField(blank=True, max_length=200, null=True),
        ),
        migrations.AddField(
            model_name='template_type_tech',
            name='version_tag',
            field=models.CharField(blank=True, max_length=200, null=True),
        ),
        migrations.AlterField(
            model_name='template_type_variable',
            name='units',
            field=models.CharField(blank=True, max_length=200, null=True),
        ),
    ]