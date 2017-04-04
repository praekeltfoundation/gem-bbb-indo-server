# -*- coding: utf-8 -*-
# Generated by Django 1.10.5 on 2017-03-30 12:10
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('content', '0089_merge_20170323_1242'),
    ]

    operations = [
        migrations.AddField(
            model_name='budget',
            name='expenses_decreased_count',
            field=models.IntegerField(default=0, verbose_name='total expenses decreased count'),
        ),
        migrations.AddField(
            model_name='budget',
            name='expenses_increased_count',
            field=models.IntegerField(default=0, verbose_name='total expenses increased count'),
        ),
        migrations.AddField(
            model_name='budget',
            name='expenses_modified',
            field=models.DateTimeField(editable=False, null=True, verbose_name='total expenses modified on'),
        ),
        migrations.AddField(
            model_name='budget',
            name='income_decreased_count',
            field=models.IntegerField(default=0, verbose_name='income decreased count'),
        ),
        migrations.AddField(
            model_name='budget',
            name='income_increased_count',
            field=models.IntegerField(default=0, verbose_name='income increase count'),
        ),
        migrations.AddField(
            model_name='budget',
            name='income_modified',
            field=models.DateTimeField(editable=False, null=True, verbose_name='income modified on'),
        ),
        migrations.AddField(
            model_name='budget',
            name='modified_on',
            field=models.DateTimeField(blank=True, editable=False, null=True),
        ),
        migrations.AddField(
            model_name='budget',
            name='original_expenses',
            field=models.DecimalField(decimal_places=2, editable=False, max_digits=18, null=True, verbose_name='original total expenses'),
        ),
        migrations.AddField(
            model_name='budget',
            name='original_income',
            field=models.DecimalField(decimal_places=2, editable=False, max_digits=18, null=True, verbose_name='original income'),
        ),
        migrations.AddField(
            model_name='budget',
            name='original_savings',
            field=models.DecimalField(decimal_places=2, editable=False, max_digits=18, null=True, verbose_name='original savings'),
        ),
        migrations.AddField(
            model_name='budget',
            name='savings_decreased_count',
            field=models.IntegerField(default=0, verbose_name='savings decreased count'),
        ),
        migrations.AddField(
            model_name='budget',
            name='savings_increased_count',
            field=models.IntegerField(default=0, verbose_name='savings increased count'),
        ),
        migrations.AddField(
            model_name='budget',
            name='savings_modified',
            field=models.DateTimeField(editable=False, null=True, verbose_name='savings modified on'),
        ),
        migrations.AddField(
            model_name='expense',
            name='modified_on',
            field=models.DateTimeField(editable=False, null=True),
        ),
        migrations.AddField(
            model_name='expense',
            name='original_value',
            field=models.DecimalField(decimal_places=2, editable=False, max_digits=18, null=True, verbose_name='original value'),
        ),
        migrations.AddField(
            model_name='expense',
            name='value_decreased_count',
            field=models.IntegerField(default=0, editable=False, verbose_name='value decreased count'),
        ),
        migrations.AddField(
            model_name='expense',
            name='value_increased_count',
            field=models.IntegerField(default=0, editable=False, verbose_name='value increased count'),
        ),
        migrations.AddField(
            model_name='expense',
            name='value_modified',
            field=models.DateTimeField(editable=False, null=True, verbose_name='value modified on'),
        ),
    ]
