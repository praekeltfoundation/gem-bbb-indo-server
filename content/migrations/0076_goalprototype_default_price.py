# -*- coding: utf-8 -*-
# Generated by Django 1.10.4 on 2017-02-02 07:45
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('content', '0075_remove_badgesettings_first_challenge_completed'),
    ]

    operations = [
        migrations.AddField(
            model_name='goalprototype',
            name='default_price',
            field=models.DecimalField(decimal_places=2, default=0.0, max_digits=18),
        ),
    ]
