# -*- coding: utf-8 -*-
# Generated by Django 1.10.2 on 2016-10-28 09:01
from __future__ import unicode_literals

from django.db import migrations


class Migration(migrations.Migration):

    replaces = [
        ('content', '0006_auto_20161028_0901'),

    ]

    dependencies = [
        ('content', '0004_auto_20161027_1309'),
        ('content', '0004_auto_20161027_1309_b'),
        ('content', '0005_questionoption_correct'),
    ]

    operations = [
        migrations.RenameModel(
            old_name='AnswerLog',
            new_name='ParticipantAnswer',
        ),
    ]