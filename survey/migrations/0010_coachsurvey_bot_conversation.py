# -*- coding: utf-8 -*-
# Generated by Django 1.10.4 on 2017-01-10 08:18
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('survey', '0009_coachsurvey_notification_body'),
    ]

    operations = [
        migrations.AddField(
            model_name='coachsurvey',
            name='bot_conversation',
            field=models.IntegerField(choices=[(0, 'none'), (1, 'baseline'), (2, 'ea tool')], default=0),
        ),
    ]
