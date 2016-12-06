# -*- coding: utf-8 -*-
# Generated by Django 1.10.2 on 2016-12-04 08:00
from __future__ import unicode_literals

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        ('content', '0052_badgesettings'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='UserBadge',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('earned_on', models.DateTimeField(default=django.utils.timezone.now)),
                ('badge', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='content.Badge')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.AddField(
            model_name='badge',
            name='user',
            field=models.ManyToManyField(related_name='badges', through='content.UserBadge', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AlterModelOptions(
            name='badge',
            options={'verbose_name': 'badge', 'verbose_name_plural': 'badges'},
        ),
        migrations.AlterField(
            model_name='badge',
            name='state',
            field=models.IntegerField(choices=[(0, 'Inactive'), (1, 'Active')], default=1),
        ),
    ]