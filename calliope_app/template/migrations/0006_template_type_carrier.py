# Generated by Django 3.2.15 on 2023-07-14 16:27

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('template', '0005_auto_20230520_0303'),
    ]

    operations = [
        migrations.CreateModel(
            name='Template_Type_Carrier',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=200)),
                ('description', models.TextField(blank=True, null=True)),
                ('rate_unit', models.CharField(max_length=20)),
                ('quantity_unit', models.CharField(max_length=20)),
                ('template_type', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='template.template_type')),
            ],
            options={
                'verbose_name_plural': '[Admin] Template Type Carriers',
                'db_table': 'template_type_carrier',
                'ordering': ['name'],
            },
        ),
    ]
