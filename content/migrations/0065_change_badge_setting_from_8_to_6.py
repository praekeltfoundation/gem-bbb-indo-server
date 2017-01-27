from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion

class Migration(migrations.Migration):
    dependencies = [
        ('content', '0064_agreementindex'),
    ]

    operations = [
        migrations.RenameField('badgesettings', 'weekly_target_8', 'weekly_target_6')
        ]