# -*- coding: utf-8 -*-
# Generated by Django 1.10.2 on 2016-10-27 13:09
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone


def from_tmp_new(apps, schema_editor):
    Question = apps.get_model('content.QuizQuestion')
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


def to_tmp_new(apps, schema_editor):
    Question = apps.get_model('content.QuizQuestion')
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


class Migration(migrations.Migration):

    replaces = [
        ('content', '0004_auto_20161027_1309_b'),
    ]

    dependencies = [
        ('content', '0004_auto_20161027_1309'),
    ]

    operations = [
        migrations.AddField(
            model_name='quizquestion',
            name='challenge',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, related_name='questions', to='content.Challenge'),
        ),
        migrations.AddField(
            model_name='questionoption',
            name='question',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, related_name='options', to='content.QuizQuestion'),
        ),
        migrations.AddField(
            model_name='questionoption',
            name='next_question',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, related_name='+', to='content.QuizQuestion'),
        ),
        migrations.AddField(
            model_name='answerlog',
            name='question',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, related_name='+', to='content.QuizQuestion'),
        ),
        migrations.RunPython(
            code=from_tmp_new,
            reverse_code=to_tmp_new,
        ),
        migrations.RemoveField(
            model_name='quizquestion',
            name='old_challenge_id',
        ),
        migrations.RemoveField(
            model_name='questionoption',
            name='old_question_id',
        ),
        migrations.RemoveField(
            model_name='questionoption',
            name='old_next_question_id',
        ),
        migrations.RemoveField(
            model_name='answerlog',
            name='old_question_id',
        ),
    ]
