# -*- coding: utf-8 -*-
# Generated by Django 1.10.2 on 2016-10-10 08:33
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('content', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='questionoption',
            name='next_question',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, related_name='+', to='content.Question'),
        ),
    ]
