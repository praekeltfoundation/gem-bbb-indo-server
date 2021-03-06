# -*- coding: utf-8 -*-
# Generated by Django 1.10.2 on 2016-10-28 09:16
from __future__ import unicode_literals

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('content', '0006_auto_20161028_0901'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='participantanswer',
            options={'verbose_name': 'participant answer', 'verbose_name_plural': 'participant answers'},
        ),
        migrations.RenameField(
            model_name='participantanswer',
            old_name='answered',
            new_name='date_answered',
        ),
        migrations.RenameField(
            model_name='participantanswer',
            old_name='saved',
            new_name='date_saved',
        ),
        migrations.RemoveField(
            model_name='participantanswer',
            name='challenge',
        ),
        migrations.RemoveField(
            model_name='participantanswer',
            name='response',
        ),
        migrations.AddField(
            model_name='participantanswer',
            name='selected_option',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, related_name='+', to='content.QuestionOption'),
        ),
        migrations.AlterField(
            model_name='participantanswer',
            name='user',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, related_name='+', to=settings.AUTH_USER_MODEL),
        ),
    ]
