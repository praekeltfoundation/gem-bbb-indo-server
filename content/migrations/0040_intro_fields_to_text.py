# -*- coding: utf-8 -*-
# Generated by Django 1.10.2 on 2016-11-25 12:47
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('content', '0039_auto_20161125_0914'),
    ]

    operations = [
        migrations.AlterField(
            model_name='challenge',
            name='call_to_action',
            field=models.TextField(blank=True, help_text='Displayed on the Challenge popup when it is not available yet.', verbose_name='call to action'),
        ),
        migrations.AlterField(
            model_name='challenge',
            name='instruction',
            field=models.TextField(blank=True, help_text='Displayed on the Challenge splash screen when it is available.', verbose_name='instructional text'),
        ),
        migrations.AlterField(
            model_name='challenge',
            name='intro',
            field=models.TextField(blank=True, help_text='The opening line said by the Coach when telling the user about the Challenge.', verbose_name='intro dialogue'),
        ),
        migrations.AlterField(
            model_name='challenge',
            name='outro',
            field=models.TextField(blank=True, help_text='The line said by the Coach when the user has completed their Challenge submission.', verbose_name='outro dialogue'),
        ),
        migrations.AlterField(
            model_name='tip',
            name='intro',
            field=models.TextField(blank=True, help_text='The opening line said by the Coach when telling the user about the Tip.', verbose_name='intro dialogue'),
        ),
    ]
