# -*- coding: utf-8 -*-
# Generated by Django 1.10.2 on 2016-10-27 08:25
from __future__ import unicode_literals

from django.db import migrations, models
import users.models
import users.storage


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0003_auto_20161021_1120'),
    ]

    operations = [
        migrations.AlterField(
            model_name='profile',
            name='profile_image',
            field=models.ImageField(null=True, storage=users.storage.OverwriteStorage('/home/newuser/praekelt/bimbingbung-server/media/protected', '/protected/'), upload_to=users.models.get_profile_image_filename),
        ),
    ]