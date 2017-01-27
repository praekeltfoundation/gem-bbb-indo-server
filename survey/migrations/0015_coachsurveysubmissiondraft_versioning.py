# -*- coding: utf-8 -*-
# Generated by Django 1.10.4 on 2017-01-26 12:46
from __future__ import unicode_literals

from django.db import migrations, models
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        ('survey', '0014_coachsurveysubmissiondraft_related_name'),
    ]

    operations = [
        migrations.AddField(
            model_name='coachsurveysubmissiondraft',
            name='created_at',
            field=models.DateTimeField(default=django.utils.timezone.now),
        ),
        migrations.AddField(
            model_name='coachsurveysubmissiondraft',
            name='modified_at',
            field=models.DateTimeField(default=django.utils.timezone.now),
        ),
        migrations.AddField(
            model_name='coachsurveysubmissiondraft',
            name='version',
            field=models.IntegerField(default=0),
        ),
    ]
