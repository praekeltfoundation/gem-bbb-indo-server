# -*- coding: utf-8 -*-
# Generated by Django 1.10.2 on 2016-11-24 13:24
from __future__ import unicode_literals

from django.db import migrations
from django.contrib.contenttypes.models import ContentType
from django.contrib.auth.models import Group, Permission


def get_content_type(apps, app_name, model_name):
    return ContentType.objects.get_for_model(apps.get_model(app_name, model_name))


def get_challenge_types(apps):
    return (
        get_content_type(apps, 'content', 'Challenge'),
        get_content_type(apps, 'content', 'QuizQuestion'),
        get_content_type(apps, 'content', 'QuestionOption'),
        get_content_type(apps, 'content', 'PictureQuestion'),
        get_content_type(apps, 'content', 'FreeTextQuestion'),

        get_content_type(apps, 'content', 'Participant'),
        get_content_type(apps, 'content', 'Entry'),
        get_content_type(apps, 'content', 'ParticipantAnswer'),
        get_content_type(apps, 'content', 'ParticipantPicture'),
        get_content_type(apps, 'content', 'ParticipantFreeText'),
    )


def add_permissions(group, challenge_content_type):
    challenge_permissions = Permission.objects.filter(content_type=challenge_content_type)

    for perm in challenge_permissions:
        group.permissions.add(perm)

    group.save()


def remove_permissions(group, challenge_content_type):
    group.permissions.filter(content_type=challenge_content_type).delete()
    group.save()


def add_challenge_permissions(apps, editor):
    editor_group = Group.objects.get(name='Editors')
    moderator_group = Group.objects.get(name='Moderators')

    for content_type in get_challenge_types(apps):
        add_permissions(editor_group, content_type)
        add_permissions(moderator_group, content_type)


def remove_challenge_permissions(apps, editor):
    editor_group = Group.objects.get(name='Editors')
    moderator_group = Group.objects.get(name='Moderators')

    for content_type in get_challenge_types(apps):
        remove_permissions(editor_group, content_type)
        remove_permissions(moderator_group, content_type)


class Migration(migrations.Migration):

    dependencies = [
        ('content', '0037_removed_challenge_agreement_link'),
    ]

    operations = [
        migrations.RunPython(add_challenge_permissions, remove_challenge_permissions),
    ]
