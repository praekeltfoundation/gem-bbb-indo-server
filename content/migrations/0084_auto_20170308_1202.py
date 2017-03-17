# -*- coding: utf-8 -*-
# Generated by Django 1.10.5 on 2017-03-08 10:02
from __future__ import unicode_literals

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('content', '0083_auto_20170306_1009'),
    ]

    operations = [
        migrations.AlterField(
            model_name='participant',
            name='user',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, related_name='participants', to=settings.AUTH_USER_MODEL),
        ),
    ]