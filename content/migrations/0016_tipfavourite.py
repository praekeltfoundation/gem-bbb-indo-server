# -*- coding: utf-8 -*-
# Generated by Django 1.10.2 on 2016-11-05 08:19
from __future__ import unicode_literals

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('content', '0015_auto_20161103_1547'),
    ]

    operations = [
        migrations.CreateModel(
            name='TipFavourite',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('state', models.IntegerField(choices=[(0, 'Disabled'), (1, 'Enabled')], default=1)),
                ('date_favourited', models.DateTimeField(verbose_name='favourited on')),
                ('date_saved', models.DateTimeField(default=django.utils.timezone.now, verbose_name='saved on')),
                ('tip', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='+', to='content.Tip')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='+', to=settings.AUTH_USER_MODEL)),
            ],
            options={'verbose_name': 'tip favourite', 'verbose_name_plural': 'tip favourites'},
        ),
    ]