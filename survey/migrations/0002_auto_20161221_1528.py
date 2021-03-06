# -*- coding: utf-8 -*-
# Generated by Django 1.10.4 on 2016-12-21 13:28
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('survey', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='coachsurvey',
            name='deliver_after',
            field=models.IntegerField(default=1, help_text='The number of days after user registration that the Survey will be available.', verbose_name='days to deliver'),
        ),
        migrations.AlterField(
            model_name='coachsurvey',
            name='intro',
            field=models.TextField(blank=True, help_text='The opening line said by the Coach when introducing the Survey.', verbose_name='intro dialogue'),
        ),
        migrations.AlterField(
            model_name='coachsurvey',
            name='outro',
            field=models.TextField(blank=True, help_text='The closing line said by the Coach when finishing the Survey.', verbose_name='outro dialogue'),
        ),
    ]
