# -*- coding: utf-8 -*-
# Generated by Django 1.10.5 on 2017-03-06 07:00
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('wagtailimages', '0013_make_rendition_upload_callable'),
        ('content', '0082_merge_20170227_1346'),
    ]

    operations = [
        migrations.CreateModel(
            name='ExpenseCategory',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100)),
                ('state', models.IntegerField(choices=[(0, 'Inactive'), (1, 'Active')], default=0)),
                ('image', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='+', to='wagtailimages.Image')),
            ],
            options={
                'verbose_name': 'expense category',
                'verbose_name_plural': 'expense categories',
            },
        ),
    ]
