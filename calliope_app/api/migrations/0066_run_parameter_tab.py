# Generated by Django 3.2.25 on 2024-04-30 19:56

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0065_computeenvironment_solver'),
    ]

    operations = [
        migrations.AddField(
            model_name='run_parameter',
            name='tab',
            field=models.TextField(blank=True, default='scenarios', null=True),
        ),
    ]