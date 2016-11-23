# -*- coding: utf-8 -*-
# Generated by Django 1.10.2 on 2016-11-18 13:39
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('content', '0030_agreement'),
    ]

    operations = [
        migrations.AddField(
            model_name='tip',
            name='intro',
            field=models.CharField(blank=True, help_text='The opening line said by the Coach when telling the user about the Tip', max_length=200, verbose_name='intro dialogue'),
        ),
    ]