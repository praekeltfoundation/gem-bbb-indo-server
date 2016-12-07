# -*- coding: utf-8 -*-
# Generated by Django 1.10.2 on 2016-12-06 10:06
from __future__ import unicode_literals

from django.db import migrations, models
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        ('content', '0056_feedback'),
    ]

    operations = [
        migrations.AlterField(
            model_name='feedback',
            name='date_created',
            field=models.DateTimeField(default=django.utils.timezone.now, verbose_name='date created'),
        ),
        migrations.AlterField(
            model_name='goaltransaction',
            name='date',
            field=models.DateTimeField(verbose_name='date'),
        ),
        migrations.AlterField(
            model_name='goaltransaction',
            name='value',
            field=models.DecimalField(decimal_places=2, max_digits=12, verbose_name='value'),
        ),
    ]