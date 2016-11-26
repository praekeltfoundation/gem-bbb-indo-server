# -*- coding: utf-8 -*-
# Generated by Django 1.10.2 on 2016-11-26 11:04
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('content', '0043_goal_proto_required_image'),
    ]

    operations = [
        migrations.AlterField(
            model_name='goal',
            name='prototype',
            field=models.OneToOneField(blank=True, default=None, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='goals', to='content.GoalPrototype'),
        ),
    ]
