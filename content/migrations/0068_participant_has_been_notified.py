# -*- coding: utf-8 -*-
# Generated by Django 1.10.5 on 2017-01-26 06:47
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('content', '0067_participant_badges'),
    ]

    operations = [
        migrations.AddField(
            model_name='participant',
            name='has_been_notified',
            field=models.BooleanField(default=False, verbose_name='has_been_notified'),
        ),
    ]
