# -*- coding: utf-8 -*-
# Generated by Django 1.10.5 on 2017-02-14 07:52
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('content', '0077_customnotifications'),
    ]

    operations = [
        migrations.AlterField(
            model_name='customnotifications',
            name='expiration_date',
            field=models.DateField(help_text='The date when the notification should stop displaying', verbose_name='End date'),
        ),
        migrations.AlterField(
            model_name='customnotifications',
            name='icon',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='+', to='wagtailimages.Image'),
        ),
        migrations.AlterField(
            model_name='customnotifications',
            name='message',
            field=models.TextField(help_text='The message shown to the user', verbose_name='message'),
        ),
        migrations.AlterField(
            model_name='customnotifications',
            name='persist',
            field=models.BooleanField(help_text='Should the notification appear every time the user opens the app or just once', verbose_name='persist'),
        ),
        migrations.AlterField(
            model_name='customnotifications',
            name='publish_date',
            field=models.DateField(help_text='The date the notification should start displaying', verbose_name='start date'),
        ),
    ]