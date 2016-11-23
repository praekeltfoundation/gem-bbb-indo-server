# -*- coding: utf-8 -*-
# Generated by Django 1.10.2 on 2016-11-24 06:38
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('content', '0033_question_wagtail_admin'),
    ]

    operations = [
        migrations.AlterField(
            model_name='participant',
            name='challenge',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, related_name='participants', to='content.Challenge'),
        ),
    ]