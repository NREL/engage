# Generated by Django 3.2.20 on 2023-10-20 13:44

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0062_auto_20230916_0429'),
    ]

    operations = [
        migrations.AlterField(
            model_name='carrier',
            name='model',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='api.model'),
        ),
    ]