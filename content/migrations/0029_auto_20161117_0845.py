# -*- coding: utf-8 -*-
# Generated by Django 1.10.2 on 2016-11-17 06:45
from __future__ import unicode_literals

from django.db import migrations
import wagtail.wagtailcore.blocks
import wagtail.wagtailcore.fields


class Migration(migrations.Migration):

    dependencies = [
        ('content', '0028_auto_20161115_1125'),
    ]

    operations = [
        migrations.AlterField(
            model_name='tip',
            name='body',
            field=wagtail.wagtailcore.fields.StreamField((('paragraph', wagtail.wagtailcore.blocks.RichTextBlock()),)),
        ),
    ]
