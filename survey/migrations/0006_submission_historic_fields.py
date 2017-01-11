# -*- coding: utf-8 -*-
# Generated by Django 1.10.4 on 2017-01-04 09:33
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('survey', '0005_rename_form_fields'),
    ]

    operations = [
        migrations.AddField(
            model_name='coachsurveysubmission',
            name='email',
            field=models.CharField(default='', max_length=150),
        ),
        migrations.AddField(
            model_name='coachsurveysubmission',
            name='mobile',
            field=models.CharField(default='', max_length=15),
        ),
        migrations.AddField(
            model_name='coachsurveysubmission',
            name='name',
            field=models.CharField(default='', max_length=100),
        ),
        migrations.AddField(
            model_name='coachsurveysubmission',
            name='username',
            field=models.CharField(default='', max_length=150),
        ),
    ]
