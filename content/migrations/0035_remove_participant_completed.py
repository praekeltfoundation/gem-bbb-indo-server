# -*- coding: utf-8 -*-
# Generated by Django 1.10.2 on 2016-11-24 06:45
from __future__ import unicode_literals

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('content', '0034_renamed_related_participants'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='participant',
            name='completed',
        ),
    ]
