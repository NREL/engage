# Generated by Django 3.2.15 on 2023-05-04 23:29

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('template', '0003_auto_20230422_0406'),
    ]

    operations = [
        migrations.AddField(
            model_name='template_type_tech',
            name='energy_carrier',
            field=models.CharField(blank=True, max_length=200, null=True),
        ),
    ]