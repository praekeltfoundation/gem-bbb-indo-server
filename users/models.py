
from datetime import timedelta
import uuid

from django.utils import timezone
from django.utils.translation import ugettext_lazy as _
from django.utils.html import format_html
from django.contrib.auth.models import User
from django.core.validators import MinLengthValidator, RegexValidator
from django.db import models
from django.db.models.signals import pre_save, post_save
from django.dispatch import receiver
from django.utils.encoding import python_2_unicode_compatible
from rest_framework.authtoken.models import Token

from .storage import ProfileImgStorage
from content.models import Entry, Participant

from wagtail.wagtailadmin import edit_handlers as wagtail_edit_handlers
from content.edit_handlers import ReadOnlyPanel


# proxy managers
class RegUserManager(models.Manager):
    def get_queryset(self):
        return super(RegUserManager, self).get_queryset().filter(is_staff=False, is_superuser=False)

    def create(self, **kwargs):
        kwargs.update({'is_staff': False, 'is_superuser': False})
        return super(RegUserManager, self).create(**kwargs)


class SysAdminUserManager(models.Manager):
    def get_queryset(self):
        return super(SysAdminUserManager, self).get_queryset().filter(is_staff=True, is_superuser=True)

    def create(self, **kwargs):
        kwargs.update({'is_staff': True, 'is_superuser': True})
        return super(SysAdminUserManager, self).create(**kwargs)


# Users registered by mobile phone
class RegUser(User):
    objects = RegUserManager()

    class Meta:
        proxy = True

        # Translators: Collection name on CMS
        verbose_name = _('regular user')

        # Translators: Plural collection name on CMS
        verbose_name_plural = _('regular users')


# System administrators
class SysAdminUser(User):
    objects = SysAdminUserManager()

    class Meta:
        proxy = True

        # Translators: Collection name on CMS
        verbose_name = _('system administrator')

        # Translators: Plural collection name on CMS
        verbose_name_plural = _('system administrators')


def get_profile_image_filename(instance, filename):
    return '/'.join(('profile', '{}-{}'.format(instance.user.pk, filename)))


# user profile information
@python_2_unicode_compatible
class Profile(models.Model):
    # constants
    text_min_length = 6

    # gender enum
    GENDER_MALE = 0
    GENDER_FEMALE = 1

    # validators
    mobile_regex = RegexValidator(
        regex=r'^\+?1?\d{9,15}$',
        # Translators: Validation failure message
        message=_("Phone number must be entered in the format: '+999999999'. Up to 15 digits allowed."))


    # Translators: CMS field
    age = models.IntegerField(_('age'), blank=True, null=True)

    gender = models.IntegerField(choices=(
        # Translators: Gender value
        (GENDER_MALE, _('Male')),
        # Translators: Gender value
        (GENDER_FEMALE, _('Female')),
    ), blank=True, null=True)

    # Translators: CMS field name
    mobile = models.CharField(_('mobile number'), validators=[mobile_regex], max_length=15, blank=True)

    # Translators: CMS field name
    profile_image = models.ImageField(_('profile image'),
                                      upload_to=get_profile_image_filename,
                                      storage=ProfileImgStorage(),
                                      null=True,
                                      blank=True)

    # Translators: CMS field name
    security_question = models.TextField(
        _('security question'),
        blank=False,
        null=True,
        validators=[
            MinLengthValidator(
                text_min_length,
                # Translators: Validation failure message
                _('Security question must be at least %d characters long') % (text_min_length,))])

    # Translators: CMS field name
    security_question_answer = models.TextField(
        _('security question answer'),
        blank=False,
        null=True)

    user = models.OneToOneField(User, on_delete=models.CASCADE)

    class Meta:
        # Translators: Collection name on CMS
        verbose_name = _('profile')

        # Translators: Plural collection name on CMS
        verbose_name_plural = _('profiles')

    def __str__(self):
        return self.mobile

    def set_security_question(self, new_question, new_answer):
        self.security_question = new_question
        self.security_question_answer = new_answer
        self.save()

    def verify_security_question(self, answer):
        return answer == self.security_question_answer

    @property
    def joined_days(self):
        """The number of days since the user has registered"""
        return (timezone.now() - self.user.date_joined).days

    def is_joined_days_passed(self, days):
        """Checks whether a provided number of days has passed since the user has registered."""
        return timezone.now() >= self.user.date_joined + timedelta(days=days)

    def is_first_challenge_completed(self):
        """Checks to see if the user has completed at least one challenge"""
        participants = Participant.objects.filter(user_id=self.user.id)

        total_completions = 0

        total_completions += Entry.objects.filter(participant__in=participants).count()
        #total_completions += ParticipantPicture.objects.filter(participant__in=participants).count()
        #total_completions += ParticipantFreeText.objects.filter(participant__in=participants).count()

        if total_completions == 0:
            return False

        return True

class UserUUID(models.Model):

    gaid = models.UUIDField(verbose_name=_('Google Analytics ID'), editable=False, default=uuid.uuid4)

    user = models.OneToOneField(User, on_delete=models.CASCADE)


#############################
# Google Campaign Analytics #
#############################


class CampaignInformation(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    user_uuid = models.OneToOneField(UserUUID, on_delete=models.CASCADE)

    campaign = models.TextField(_('campaign'), blank=False, null=True)
    source = models.TextField(_('source'), blank=False, null=True)
    medium = models.TextField(_('medium'), blank=False, null=True)


###############################
# Endline Survey User Chooser #
###############################


class EndlineSurveySelectUsers(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    receive_survey = models.BooleanField(default=False, help_text=_('Should the user receive the Endline Survey'))
    survey_completed = models.BooleanField(default=False, help_text=_('Has the user already completed the survey'))

    def mark_receive_survey(self):
        if self.receive_survey:
            return format_html(
                "<input type='checkbox' id='{}' class='mark-receive-survey' value='{}' checked='checked' />",
                'participant-is-shortlisted-%d' % self.id, self.id)
        else:
            return format_html("<input type='checkbox' id='{}' class='mark-receive-survey' value='{}' />",
                               'participant-is-shortlisted-%d' % self.id, self.id)

EndlineSurveySelectUsers.panels = [
    wagtail_edit_handlers.MultiFieldPanel([
        wagtail_edit_handlers.FieldPanel('user'),
        wagtail_edit_handlers.FieldPanel('receive_survey'),
        ReadOnlyPanel('survey_completed',)
    ])
]


def reset_token(sender, instance, **kwargs):
    """Invalidates a token when a user's password is changed."""
    new_password = instance.password

    try:
        old_password = User.objects.get(pk=instance.pk).password
    except User.DoesNotExist:
        old_password = None

    if new_password != old_password:
        Token.objects.filter(user=instance).delete()


# Django signals do not consider subclasses of the sender. When connected using User, RegUser will not trigger the
# handler. Each model is registered separately.
MODEL_CLASSES = (User, RegUser, SysAdminUser)
for model in MODEL_CLASSES:
    pre_save.connect(reset_token, model)


@receiver(post_save, sender=User)
def create_profile(sender, instance, created, **kwargs):
    if created:
        Profile.objects.create(user=instance)
        EndlineSurveySelectUsers.objects.get_or_create(user=instance)


@receiver(post_save, sender=User)
def save_profile(sender, instance, **kwargs):
    instance.profile.save()
