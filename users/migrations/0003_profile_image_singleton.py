# -*- coding: utf-8 -*-
# Generated by Django 1.10.2 on 2016-11-02 07:58
from __future__ import unicode_literals

from django.db import migrations, models
import users.models
import users.storage


class Migration(migrations.Migration):

    replaces = [
        ('users', '0003_auto_20161021_1120'),
        ('users', '0004_auto_20161027_0825'),
        ('users', '0005_auto_20161102_0758'),
    ]

    dependencies = [
        ('users', '0002_profile_profile_image'),
    ]

    operations = [
        migrations.AlterField(
            model_name='profile',
            name='profile_image',
            field=models.ImageField(blank=True, null=True, storage=users.storage.ProfileImgStorage(), upload_to=users.models.get_profile_image_filename),
        ),
    ]
