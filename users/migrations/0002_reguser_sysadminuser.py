# -*- coding: utf-8 -*-
# Generated by Django 1.10.2 on 2016-10-05 09:08
from __future__ import unicode_literals

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('auth', '0008_alter_user_username_max_length'),
        ('users', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='RegUser',
            fields=[
            ],
            options={
                'verbose_name_plural': 'Regular users',
                'verbose_name': 'Regular user',
                'proxy': True,
            },
            bases=('auth.user',),
        ),
        migrations.CreateModel(
            name='SysAdminUser',
            fields=[
            ],
            options={
                'verbose_name_plural': 'System administrators',
                'verbose_name': 'System administrator',
                'proxy': True,
            },
            bases=('auth.user',),
        ),
    ]
