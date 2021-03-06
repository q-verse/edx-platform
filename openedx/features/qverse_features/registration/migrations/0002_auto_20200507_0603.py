# -*- coding: utf-8 -*-
# Generated by Django 1.11.21 on 2020-05-07 10:03
from __future__ import unicode_literals

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('registration', '0001_initial'),
    ]

    operations = [
        migrations.RenameModel(
            old_name='AdmissionData',
            new_name='BulkUserRegistration',
        ),
        migrations.RemoveField(
            model_name='prospectiveuser',
            name='department',
        ),
        migrations.AlterModelOptions(
            name='bulkuserregistration',
            options={},
        ),
        migrations.AlterModelOptions(
            name='qverseuserprofile',
            options={'verbose_name_plural': 'Qverse User Profiles'},
        ),
        migrations.RemoveField(
            model_name='qverseuserprofile',
            name='first_name',
        ),
        migrations.RemoveField(
            model_name='qverseuserprofile',
            name='surname',
        ),
        migrations.DeleteModel(
            name='ProspectiveUser',
        ),
    ]
