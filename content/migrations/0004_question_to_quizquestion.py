# -*- coding: utf-8 -*-
# Generated by Django 1.10.2 on 2016-10-27 13:09
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone


def to_tmp_old(apps, schema_editor):
    Question = apps.get_model('content.Question')
    QuestionOption = apps.get_model('content.QuestionOption')
    AnswerLog = apps.get_model('content.AnswerLog')
    for question in Question.objects.all():
        question.old_challenge_id = question.challenge_id
        question.save()
    for option in QuestionOption.objects.all():
        option.old_question_id = option.question_id
        option.old_next_question_id = option.next_question_id
        option.save()
    for answer in AnswerLog.objects.all():
        answer.old_question_id = answer.question_id
        answer.save()


def from_tmp_old(apps, schema_editor):
    Question = apps.get_model('content.Question')
    QuestionOption = apps.get_model('content.QuestionOption')
    AnswerLog = apps.get_model('content.AnswerLog')
    for question in Question.objects.all():
        question.challenge_id = question.old_challenge_id
        question.save()
    for option in QuestionOption.objects.all():
        option.question_id = option.old_question_id
        option.next_question_id = option.old_next_question_id
        option.save()
    for answer in AnswerLog.objects.all():
        answer.question_id = answer.old_question_id
        answer.save()


class Migration(migrations.Migration):

    replaces = [
        ('content', '0004_auto_20161027_1309'),
    ]

    dependencies = [
        ('content', '0003_tag_tip_squashed_0006_auto_20161011_1314'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='answerlog',
            options={'verbose_name': 'user answer log', 'verbose_name_plural': 'user answers'},
        ),
        migrations.AlterModelOptions(
            name='challenge',
            options={'verbose_name': 'challenge', 'verbose_name_plural': 'challenges'},
        ),
        migrations.AlterModelOptions(
            name='questionoption',
            options={'verbose_name': 'question option', 'verbose_name_plural': 'question options'},
        ),
        migrations.AlterModelOptions(
            name='tip',
            options={'verbose_name': 'tip', 'verbose_name_plural': 'tips'},
        ),
        migrations.AddField(
            model_name='challenge',
            name='type',
            field=models.PositiveIntegerField(choices=[(1, 'Quiz'), (2, 'Picture'), (3, 'Free text')], default=1, verbose_name='type'),
        ),
        migrations.AlterField(
            model_name='answerlog',
            name='answered',
            field=models.DateTimeField(verbose_name='answered on'),
        ),
        migrations.AlterField(
            model_name='answerlog',
            name='question',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, related_name='+', to='content.Question'),
        ),
        migrations.AlterField(
            model_name='answerlog',
            name='response',
            field=models.TextField(blank=True, verbose_name='response'),
        ),
        migrations.AlterField(
            model_name='answerlog',
            name='saved',
            field=models.DateTimeField(default=django.utils.timezone.now, verbose_name='saved on'),
        ),
        migrations.AlterField(
            model_name='answerlog',
            name='user',
            field=models.TextField(blank=True, verbose_name='user ID'),
        ),
        migrations.AlterField(
            model_name='challenge',
            name='activation_date',
            field=models.DateTimeField(verbose_name='activate on'),
        ),
        migrations.AlterField(
            model_name='challenge',
            name='deactivation_date',
            field=models.DateTimeField(verbose_name='deactivate on'),
        ),
        migrations.AlterField(
            model_name='challenge',
            name='end_processed',
            field=models.BooleanField(default=False, verbose_name='processed'),
        ),
        migrations.AlterField(
            model_name='challenge',
            name='name',
            field=models.CharField(max_length=30, verbose_name='challenge name'),
        ),
        migrations.AlterField(
            model_name='challenge',
            name='state',
            field=models.PositiveIntegerField(choices=[(1, 'Incomplete'), (2, 'Ready for review'), (3, 'Published'), (4, 'Done')], default=1, verbose_name='state'),
        ),
        migrations.AlterField(
            model_name='questionoption',
            name='name',
            field=models.TextField(null=True, verbose_name='name'),
        ),
        migrations.AlterField(
            model_name='questionoption',
            name='next_question',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, related_name='+', to='content.Question'),
        ),
        migrations.AlterField(
            model_name='questionoption',
            name='picture',
            field=models.URLField(blank=True, null=True, verbose_name='picture URL'),
        ),
        migrations.AlterField(
            model_name='questionoption',
            name='question',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, related_name='+', to='content.Question'),
        ),
        migrations.AlterField(
            model_name='questionoption',
            name='text',
            field=models.TextField(blank=True, verbose_name='text'),
        ),
        migrations.RemoveField(
            model_name='question',
            name='picture',
        ),
        migrations.RemoveField(
            model_name='question',
            name='type',
        ),
        migrations.AlterField(
            model_name='question',
            name='name',
            field=models.TextField('name', blank=True, null=False, unique=True),
        ),
        migrations.AlterField(
            model_name='question',
            name='order',
            field=models.PositiveIntegerField('order', default=0),
        ),
        migrations.AlterField(
            model_name='question',
            name='text',
            field=models.TextField('text', blank=True),
        ),
        migrations.AddField(
            model_name='question',
            name='old_challenge_id',
            field=models.PositiveIntegerField(null=True),
        ),
        migrations.AddField(
            model_name='questionoption',
            name='old_question_id',
            field=models.PositiveIntegerField(null=True),
        ),
        migrations.AddField(
            model_name='questionoption',
            name='old_next_question_id',
            field=models.PositiveIntegerField(null=True),
        ),
        migrations.AddField(
            model_name='answerlog',
            name='old_question_id',
            field=models.PositiveIntegerField(null=True),
        ),
        migrations.RunPython(
            code=to_tmp_old,
            reverse_code=from_tmp_old,
        ),
        migrations.RemoveField(
            model_name='question',
            name='challenge',
        ),
        migrations.RemoveField(
            model_name='questionoption',
            name='question',
        ),
        migrations.RemoveField(
            model_name='questionoption',
            name='next_question',
        ),
        migrations.RemoveField(
            model_name='answerlog',
            name='question',
        ),
        migrations.RenameModel(
            old_name='Question',
            new_name='QuizQuestion'),
        migrations.AlterModelOptions(
            name='quizquestion',
            options={'verbose_name': 'question', 'verbose_name_plural': 'questions'},
        ),
    ]
