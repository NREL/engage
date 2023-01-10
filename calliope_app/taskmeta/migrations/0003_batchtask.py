# Generated by Django 3.2.13 on 2022-06-02 22:02

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('taskmeta', '0002_alter_celerytask_result'),
    ]

    operations = [
        migrations.CreateModel(
            name='BatchTask',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('task_id', models.CharField(editable=False, max_length=36, null=True)),
                ('status', models.CharField(choices=[('SUBMITTED', 'SUBMITTED'), ('PENDING', 'PENDING'), ('RUNNABLE', 'RUNNABLE'), ('STARTEDING', 'STARTEDING'), ('RUNNING', 'RUNNING'), ('SUCCEEDED', 'SUCCEEDED'), ('FAILED', 'FAILED')], default=None, max_length=20)),
                ('date_start', models.DateTimeField(editable=False, null=True)),
                ('date_done', models.DateTimeField(editable=False, null=True)),
                ('result', models.JSONField(default=None, null=True)),
                ('traceback', models.TextField(default=None, null=True)),
            ],
            options={
                'verbose_name_plural': '[Admin] Batch Task',
                'db_table': 'batch_task',
            },
        ),
    ]
