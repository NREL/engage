# Generated by Django 2.2.24 on 2022-03-02 05:45

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('api', '0053_run_manual'),
    ]

    operations = [
        migrations.CreateModel(
            name='ComputeEnvironment',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=120)),
                ('alias', models.CharField(blank=True, max_length=120, null=True)),
                ('is_default', models.BooleanField(default=False)),
                ('type', models.CharField(choices=[('Celery Worker', 'Celery Worker'), ('Container Job', 'Container Job'), ('Other Compute', 'Other Compute')], max_length=60)),
                ('ncpu', models.PositiveSmallIntegerField()),
                ('memory', models.PositiveSmallIntegerField()),
                ('users', models.ManyToManyField(blank=True, related_name='compute_environments', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name_plural': '[Admin] Compute Environments',
                'db_table': 'compute_environments',
            },
        ),
        migrations.AddField(
            model_name='run',
            name='compute_environment',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='api.ComputeEnvironment'),
        ),
    ]