# -*- coding: utf-8 -*-
# Generated by Django 1.10.2 on 2016-11-06 11:29
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('content', '0019_tip_favourites_related_name'),
    ]

    operations = [
        migrations.AlterField(
            model_name='goaltransaction',
            name='date',
            field=models.DateTimeField(),
        ),
    ]