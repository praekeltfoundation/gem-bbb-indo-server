from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion

class Migration(migrations.Migration):
    dependencies = [
        ('content', '0064_agreementindex'),
    ]

    operations = [
        migrations.RenameField('badgesettings', 'weekly_target_8', 'weekly_target_6'),
        migrations.AlterField(
            model_name='badgesettings',
            name='weekly_target_6',
            field=models.ForeignKey(help_text='Awarded when a user has reached their weekly target 6 weeks in a row.', null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='+', to='content.Badge', verbose_name='6 Week On Target'))
        ]