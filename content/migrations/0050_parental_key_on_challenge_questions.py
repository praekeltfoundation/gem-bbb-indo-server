# -*- coding: utf-8 -*-
# Generated by Django 1.10.2 on 2016-12-02 13:32
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion
import modelcluster.fields


class Migration(migrations.Migration):

    replaces = [('content', '0050_auto_20161202_1310'), ('content', '0051_auto_20161202_1320'), ('content', '0052_auto_20161202_1323'), ('content', '0053_auto_20161202_1324'), ('content', '0054_auto_20161202_1329')]

    dependencies = [
        ('content', '0049_goal_state'),
    ]

    operations = [
        migrations.AlterField(
            model_name='freetextquestion',
            name='challenge',
            field=modelcluster.fields.ParentalKey(null=True, on_delete=django.db.models.deletion.CASCADE, related_name='freetext_question', to='content.Challenge', unique=True),
        ),
        migrations.AlterField(
            model_name='picturequestion',
            name='challenge',
            field=modelcluster.fields.ParentalKey(null=True, on_delete=django.db.models.deletion.CASCADE, related_name='picture_question', to='content.Challenge', unique=True),
        ),
    ]