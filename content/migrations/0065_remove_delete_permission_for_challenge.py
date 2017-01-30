from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType
from django.db import migrations


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


def add_delete_permissions(group, challenge_content_type):
    challenge_permissions = Permission.objects.filter(content_type=challenge_content_type, name__contains="delete")

    for perm in challenge_permissions:
        group.permissions.add(perm)

    group.save()


def remove_delete_permissions(group, challenge_content_type):
    group.permissions.filter(content_type=challenge_content_type, name__contains="delete").delete()
    group.save()


def remove_challenge_delete_permission(apps, editor):
    editor_group = Group.objects.get(name='Editors')
    moderator_group = Group.objects.get(name='Moderators')

    for content_type in get_challenge_types(apps):
        remove_delete_permissions(editor_group, content_type)
        remove_delete_permissions(moderator_group, content_type)


def restore_challenge_delete_permission(apps, editor):
    editor_group = Group.objects.get(name='Editors')
    moderator_group = Group.objects.get(name='Moderators')

    for content_type in get_challenge_types(apps):
        add_delete_permissions(editor_group, content_type)
        add_delete_permissions(moderator_group, content_type)


class Migration(migrations.Migration):
    dependencies = [
        ('content', '0038_challenge_permissions'),
        ('content', '0064_agreementindex'),
    ]

    operations = [
        migrations.RunPython(remove_challenge_delete_permission, restore_challenge_delete_permission),
    ]
