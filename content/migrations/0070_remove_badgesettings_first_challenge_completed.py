# -*- coding: utf-8 -*-
# Generated by Django 1.10.4 on 2017-01-28 13:10
from __future__ import unicode_literals

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('content', '0069_badgesettings_first_challenge_completed'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='badgesettings',
            name='first_challenge_completed',
        ),
    ]