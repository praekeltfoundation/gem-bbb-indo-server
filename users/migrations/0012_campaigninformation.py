# -*- coding: utf-8 -*-
# Generated by Django 1.10.5 on 2017-03-30 07:53
from __future__ import unicode_literals

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('users', '0011_auto_20170203_1321'),
    ]

    operations = [
        migrations.CreateModel(
            name='CampaignInformation',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('campaign', models.TextField(null=True, verbose_name='campaign')),
                ('source', models.TextField(null=True, verbose_name='source')),
                ('medium', models.TextField(null=True, verbose_name='medium')),
                ('user', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
                ('user_uuid', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, to='users.UserUUID')),
            ],
        ),
    ]
