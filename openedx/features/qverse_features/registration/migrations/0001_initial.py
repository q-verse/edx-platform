# -*- coding: utf-8 -*-
# Generated by Django 1.11.29 on 2020-04-17 09:00
from __future__ import unicode_literals

from django.conf import settings
import django.core.validators
from django.db import migrations, models
import django.db.models.deletion
import openedx.features.qverse_features.registration.validators


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='AdmissionData',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('admission_file', models.FileField(null=True, upload_to='qverse_registration_csvs/', validators=[openedx.features.qverse_features.registration.validators.validate_admission_file])),
                ('description', models.CharField(max_length=100, null=True)),
            ],
            options={
                'verbose_name_plural': 'Admission data',
            },
        ),
        migrations.CreateModel(
            name='Department',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('number', models.IntegerField(unique=True, validators=[django.core.validators.MinValueValidator(1)])),
                ('name', models.CharField(max_length=50, unique=True)),
            ],
        ),
        migrations.CreateModel(
            name='ProspectiveUser',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('email', models.EmailField(max_length=254, unique=True, validators=[django.core.validators.EmailValidator])),
                ('first_name', models.CharField(max_length=20)),
                ('surname', models.CharField(max_length=20)),
                ('registration_number', models.CharField(db_index=True, max_length=30, unique=True)),
                ('other_name', models.CharField(blank=True, max_length=50)),
                ('mobile_number', models.CharField(blank=True, max_length=20)),
                ('current_level', models.IntegerField(validators=[openedx.features.qverse_features.registration.validators.validate_current_level, django.core.validators.MaxValueValidator(99)])),
                ('programme', models.IntegerField(choices=[(1, 'Undergraduate Studies'), (2, 'Postgraduate Studies'), (3, 'Matured Student Programme (MSP)'), (4, 'Diploma'), (5, 'Pre-Science'), (6, 'Sandwish')], db_index=True, validators=[openedx.features.qverse_features.registration.validators.validate_programme_choices])),
                ('department', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to='registration.Department')),
            ],
        ),
        migrations.CreateModel(
            name='QVerseUserProfile',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('first_name', models.CharField(max_length=20)),
                ('surname', models.CharField(max_length=20)),
                ('registration_number', models.CharField(db_index=True, max_length=30, unique=True)),
                ('other_name', models.CharField(blank=True, max_length=50)),
                ('mobile_number', models.CharField(blank=True, max_length=20)),
                ('current_level', models.IntegerField(choices=[(1, 'Year 1'), (2, 'Year 2'), (3, 'Year 3'), (4, 'Year 4'), (5, 'Year 5'), (6, 'Year 6'), (7, 'Year 7'), (8, 'Year 8'), (9, 'Year 9')], validators=[openedx.features.qverse_features.registration.validators.validate_current_level, django.core.validators.MaxValueValidator(99)])),
                ('programme', models.IntegerField(choices=[(1, 'Undergraduate Studies'), (2, 'Postgraduate Studies'), (3, 'Matured Student Programme (MSP)'), (4, 'Diploma'), (5, 'Pre-Science'), (6, 'Sandwish')], db_index=True, validators=[openedx.features.qverse_features.registration.validators.validate_programme_choices])),
                ('department', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to='registration.Department')),
                ('user', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='qverse_profile', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name_plural': 'Qverse user profiles',
            },
        ),
    ]
