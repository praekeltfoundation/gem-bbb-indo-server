# -*- coding: utf-8 -*-
# Generated by Django 1.10.2 on 2016-11-28 14:55
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('content', '0045_goal_prototype_capital'),
    ]

    operations = [
        migrations.AlterField(
            model_name='challenge',
            name='subtitle',
            field=models.CharField(blank=True, max_length=255, verbose_name='subtitle'),
        ),
    ]
