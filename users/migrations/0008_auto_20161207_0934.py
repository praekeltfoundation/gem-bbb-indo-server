# -*- coding: utf-8 -*-
# Generated by Django 1.10.2 on 2016-12-07 09:34
from __future__ import unicode_literals

import django.core.validators
from django.db import migrations, models
import users.models
import users.storage


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0007_profile_age_gender'),
    ]

    operations = [
        migrations.AddField(
            model_name='profile',
            name='security_question',
            field=models.TextField(null=True, validators=[django.core.validators.MinLengthValidator(6, 'Security question must be at least 6 characters long')], verbose_name='security question'),
        ),
        migrations.AddField(
            model_name='profile',
            name='security_question_answer',
            field=models.TextField(null=True, validators=[django.core.validators.MinLengthValidator(6, 'Security question answer must be at least 6 characters long')], verbose_name='security question answer'),
        ),
        migrations.AlterField(
            model_name='profile',
            name='age',
            field=models.IntegerField(blank=True, null=True, verbose_name='age'),
        ),
        migrations.AlterField(
            model_name='profile',
            name='mobile',
            field=models.CharField(blank=True, max_length=15, validators=[django.core.validators.RegexValidator(message="Phone number must be entered in the format: '+999999999'. Up to 15 digits allowed.", regex='^\\+?1?\\d{9,15}$')], verbose_name='mobile number'),
        ),
        migrations.AlterField(
            model_name='profile',
            name='profile_image',
            field=models.ImageField(blank=True, null=True, storage=users.storage.ProfileImgStorage(), upload_to=users.models.get_profile_image_filename, verbose_name='profile image'),
        ),
    ]
