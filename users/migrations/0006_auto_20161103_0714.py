# -*- coding: utf-8 -*-
# Generated by Django 1.10.2 on 2016-11-03 07:14
from __future__ import unicode_literals

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0004_auto_20161102_0758'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='profile',
            options={'verbose_name': 'profile', 'verbose_name_plural': 'profiles'},
        ),
        migrations.AlterModelOptions(
            name='reguser',
            options={'verbose_name': 'regular user', 'verbose_name_plural': 'regular users'},
        ),
        migrations.AlterModelOptions(
            name='sysadminuser',
            options={'verbose_name': 'system administrator', 'verbose_name_plural': 'system administrators'},
        ),
    ]
