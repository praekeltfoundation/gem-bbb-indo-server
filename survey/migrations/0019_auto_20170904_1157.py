# -*- coding: utf-8 -*-
# Generated by Django 1.10.7 on 2017-09-04 09:57
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('survey', '0018_coachsurveysubmission_survey'),
    ]

    operations = [
        migrations.AlterField(
            model_name='coachsurvey',
            name='bot_conversation',
            field=models.IntegerField(choices=[(0, 'none'), (1, 'baseline'), (2, 'ea tool'), (3, 'endline')], default=0),
        ),
    ]
