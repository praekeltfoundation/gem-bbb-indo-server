# -*- coding: utf-8 -*-
# Generated by Django 1.10.4 on 2017-01-26 14:06
from __future__ import unicode_literals

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('survey', '0015_coachsurveysubmissiondraft_versioning'),
    ]

    operations = [
        migrations.RenameField(
            model_name='coachsurveysubmissiondraft',
            old_name='submission',
            new_name='submission_data',
        ),
    ]
