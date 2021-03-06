# -*- coding: utf-8 -*-
# Generated by Django 1.10.2 on 2016-12-04 08:49
from __future__ import unicode_literals

from django.conf import settings
from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('content', '0053_userbadge'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='userbadge',
            options={'verbose_name': 'user badge', 'verbose_name_plural': 'user badges'},
        ),
        migrations.AlterUniqueTogether(
            name='userbadge',
            unique_together=set([('user', 'badge')]),
        ),
    ]
