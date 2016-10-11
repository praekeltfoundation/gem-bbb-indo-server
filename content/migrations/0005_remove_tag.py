# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('content', '0004_auto_20161011_1002'),
    ]

    operations = [
        migrations.DeleteModel('Tag'),
        migrations.DeleteModel('TipTag'),
    ]
