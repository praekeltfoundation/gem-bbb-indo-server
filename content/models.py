from collections import OrderedDict
from datetime import timedelta
from functools import reduce
from math import ceil, floor
from os.path import splitext
from uuid import uuid4

from django.apps import apps
from django.contrib.auth.models import User
from django.db import models
from django.db.models import Count
import datetime
from django.utils import timezone
from django.utils.encoding import python_2_unicode_compatible
from django.utils.html import format_html
from django.utils.translation import ugettext as _
from modelcluster import fields as modelcluster_fields
from modelcluster.contrib.taggit import ClusterTaggableManager
from taggit.models import TaggedItemBase
from wagtail.contrib.settings.models import BaseSetting, register_setting
from wagtail.wagtailadmin import edit_handlers as wagtail_edit_handlers
from wagtail.wagtailcore import blocks as wagtail_blocks
from wagtail.wagtailcore import fields as wagtail_fields
from wagtail.wagtailcore import models as wagtail_models
from wagtail.wagtailimages import edit_handlers as wagtail_image_edit
from wagtail.wagtailimages import models as wagtail_image_models

from .storage import ChallengeStorage, GoalImgStorage, ParticipantPictureStorage

# ======== #
# Settings #
# ======== #


WEEK_STREAK_2 = 2
WEEK_STREAK_4 = 4
WEEK_STREAK_6 = 6
WEEKLY_TARGET_2 = 2
WEEKLY_TARGET_4 = 4
WEEKLY_TARGET_6 = 6


@register_setting
class BadgeSettings(BaseSetting):
    goal_first_created = models.ForeignKey(
        'Badge',
        verbose_name=_('First Goal Created'),
        related_name='+',
        on_delete=models.SET_NULL,
        help_text=_("Awarded to users when they create their first Goal."),
        blank=False, null=True
    )

    goal_half = models.ForeignKey(
        'Badge',
        verbose_name=_('First Goal Half Way'),
        related_name='+',
        on_delete=models.SET_NULL,
        help_text=_("Awarded to users when they are half-way through their first Goal."),
        blank=False, null=True
    )

    goal_week_left = models.ForeignKey(
        'Badge',
        verbose_name=_('One Week Left'),
        related_name='+',
        on_delete=models.SET_NULL,
        help_text=_("Awarded to users when they have one week left to save on their first Goal."),
        blank=False, null=True
    )

    goal_first_done = models.ForeignKey(
        'Badge',
        verbose_name=_('First Goal Done'),
        related_name='+',
        on_delete=models.SET_NULL,
        help_text=_("Awarded to users when they reach their first Goal."),
        blank=False, null=True
    )

    transaction_first = models.ForeignKey(
        'Badge',
        verbose_name=_('First Saving'),
        related_name='+',
        on_delete=models.SET_NULL,
        help_text=_("Awarded to users when they create their first savings transaction."),
        blank=False, null=True
    )

    streak_2 = models.ForeignKey(
        'Badge',
        verbose_name=_('2 Week Streak'),
        related_name='+',
        on_delete=models.SET_NULL,
        help_text=_("Awarded when a user has saved for 2 weeks."),
        blank=False, null=True
    )

    streak_4 = models.ForeignKey(
        'Badge',
        verbose_name=_('4 Week Streak'),
        related_name='+',
        on_delete=models.SET_NULL,
        help_text=_("Awarded when a user has saved for 4 weeks."),
        blank=False, null=True
    )

    streak_6 = models.ForeignKey(
        'Badge',
        verbose_name=_('6 Week Streak'),
        related_name='+',
        on_delete=models.SET_NULL,
        help_text=_("Awarded when a user has save for 6 weeks."),
        blank=False, null=True
    )

    weekly_target_2 = models.ForeignKey(
        'Badge',
        verbose_name=_('2 Week On Target'),
        related_name='+',
        on_delete=models.SET_NULL,
        help_text=_("Awarded when a user has reached their weekly target 2 weeks in a row."),
        blank=False, null=True
    )

    weekly_target_4 = models.ForeignKey(
        'Badge',
        verbose_name=_('4 Week On Target'),
        related_name='+',
        on_delete=models.SET_NULL,
        help_text=_("Awarded when a user has reached their weekly target 4 weeks in a row."),
        blank=False, null=True
    )

    weekly_target_6 = models.ForeignKey(
        'Badge',
        verbose_name=_('6 Week On Target'),
        related_name='+',
        on_delete=models.SET_NULL,
        help_text=_("Awarded when a user has reached their weekly target 6 weeks in a row."),
        blank=False, null=True
    )

    challenge_entry = models.ForeignKey(
        'Badge',
        verbose_name=_('Challenge Participation'),
        related_name='+',
        on_delete=models.SET_NULL,
        help_text=_("Awarded when a user has participated in a Challenge."),
        blank=False, null=True
    )

    challenge_win = models.ForeignKey(
        'Badge',
        verbose_name=_('Challenge Winner'),
        related_name='+',
        on_delete=models.SET_NULL,
        help_text=_("Awarded when a user has won a Challenge."),
        blank=False, null=True
    )

    class Meta:
        verbose_name = 'Badge Setup'

    def get_streak_badge(self, weeks):
        if weeks == WEEK_STREAK_2:
            return self.streak_2
        elif weeks == WEEK_STREAK_4:
            return self.streak_4
        elif weeks == WEEK_STREAK_6:
            return self.streak_6
        else:
            return None

    def get_weekly_target_badge(self, weeks):
        if weeks == WEEKLY_TARGET_2:
            return self.weekly_target_2
        elif weeks == WEEKLY_TARGET_4:
            return self.weekly_target_4
        elif weeks == WEEKLY_TARGET_6:
            return self.weekly_target_6
        else:
            return None

    @classmethod
    def get_field_verbose_name(cls, field_name):
        return cls._meta.get_field(field_name).verbose_name


BadgeSettings.panels = [
    wagtail_edit_handlers.MultiFieldPanel([
        wagtail_edit_handlers.FieldPanel('goal_first_created'),
    ],
        # Translators: Admin field name
        heading=_("goal badges")),
    wagtail_edit_handlers.MultiFieldPanel([
        wagtail_edit_handlers.FieldPanel('goal_half'),
        wagtail_edit_handlers.FieldPanel('goal_week_left'),
        wagtail_edit_handlers.FieldPanel('goal_first_done'),
        wagtail_edit_handlers.FieldPanel('transaction_first'),
        wagtail_edit_handlers.FieldPanel('streak_2'),
        wagtail_edit_handlers.FieldPanel('streak_4'),
        wagtail_edit_handlers.FieldPanel('streak_6'),
        wagtail_edit_handlers.FieldPanel('weekly_target_2'),
        wagtail_edit_handlers.FieldPanel('weekly_target_4'),
        wagtail_edit_handlers.FieldPanel('weekly_target_6'),
    ],
        # Translators: Admin field name
        heading=_("savings badges")),
    wagtail_edit_handlers.MultiFieldPanel([
        wagtail_edit_handlers.FieldPanel('challenge_entry'),
        wagtail_edit_handlers.FieldPanel('challenge_win'),
    ],
        # Translators: Admin field name
        heading=_("challenge badges")),
]


@register_setting
class SocialMediaSettings(BaseSetting):
    facebook_app_id = models.CharField(
        # Translators: Field name on CMS
        verbose_name=_('Facebook App Id'),
        max_length=255,
        # Translators: Help text on CMS
        help_text=_("The App Id provided by Facebook via the Developer Console."),
        blank=True, null=False
    )

    class Meta:
        verbose_name = 'social media accounts'


SocialMediaSettings.panels = [
    wagtail_edit_handlers.MultiFieldPanel([
        wagtail_edit_handlers.FieldPanel('facebook_app_id'),
    ],
        # Translators: Admin field name
        heading=_("Facebook")),
]


# ========== #
# Agreements #
# ========== #


class Agreement(wagtail_models.Page):
    parent_page_types = ['AgreementIndex']
    body = wagtail_fields.RichTextField(blank=True)

    content_panels = wagtail_models.Page.content_panels + [
        wagtail_edit_handlers.FieldPanel('body')
    ]

    class Meta:
        # Translators: Collection name on CMS
        verbose_name = _('agreement')

        # Translators: Plural collection name on CMS
        verbose_name_plural = _('agreements')


class AgreementIndex(wagtail_models.Page):
    # parent_page_types = ['home.HomePage']
    subpage_types = ['Agreement']


# ========== #
# Challenges #
# ========== #


def get_challenge_image_filename(instance, filename):
    if instance and instance.pk:
        new_name = instance.pk
    else:
        new_name = uuid4().hex
    return 'challenge-{}{}'.format(new_name, splitext(filename)[-1])


@python_2_unicode_compatible
class Challenge(modelcluster_fields.ClusterableModel):
    # challenge states
    CST_INCOMPLETE = 1
    CST_REVIEW_READY = 2
    CST_PUBLISHED = 3
    CST_DONE = 4

    # challenge types
    CTP_QUIZ = 1
    CTP_PICTURE = 2
    CTP_FREEFORM = 3

    # Translators: Field name on challenge CMS
    name = models.CharField(_('challenge name'), max_length=255, null=False, blank=False)

    # Translators: Field name on CMS
    subtitle = models.CharField(_('subtitle'), max_length=255, null=False, blank=True)

    # Translators: Field name on CMS
    intro = models.TextField(_('intro dialogue'), blank=True,
                             # Translators: Help text on CMS
                             help_text=_(
                                 'The opening line said by the Coach when telling the user about the Challenge.'))

    # Translators: Field name on CMS
    outro = models.TextField(_('outro dialogue'), blank=True,
                             # Translators: Help text on CMS
                             help_text=_(
                                 'The line said by the Coach when the user has completed their Challenge submission.'))

    # Translators: Field name on CMS
    call_to_action = models.TextField(_('call to action'), blank=True,
                                      # Translators: Help text on CMS
                                      help_text=_('Displayed on the Challenge popup when it is not available yet.'))

    # Translators: Field name on CMS
    instruction = models.TextField(_('instructional text'), blank=True,
                                   # Translators: Help text on CMS
                                   help_text=_('Displayed on the Challenge splash screen when it is available.'))

    # Translators: Field name on CMS (pertains to dates)
    activation_date = models.DateTimeField(_('activate on'))

    # Translators: Field name on CMS (pertains to dates)
    deactivation_date = models.DateTimeField(_('deactivate on'))
    # challenge_badge = models.ForeignKey('', null=True, blank=True)

    state = models.PositiveIntegerField(
        # Translators: Field name on CMS (state of the object, not location)
        _('state'), choices=(
            # Translators: CMS state value
            (CST_INCOMPLETE, _('Incomplete')),
            # Translators: CMS state value
            (CST_REVIEW_READY, _('Ready for review')),
            # Translators: CMS state value
            (CST_PUBLISHED, _('Published')),
            # Translators: CMS state value
            (CST_DONE, _('Done')),
        ),
        default=CST_INCOMPLETE)
    type = models.PositiveIntegerField(
        # Translators: Field name on challenge CMS (type of object)
        _('type'), choices=(
            # Translators: Challenge type
            (CTP_QUIZ, _('Quiz')),
            # Translators: Challenge type
            (CTP_PICTURE, _('Picture')),
            # Translators: Challenge type
            (CTP_FREEFORM, _('Free text')),
        ),
        default=CTP_QUIZ)

    # Translators: Field name on CMS
    picture = models.ImageField(_('picture'),
                                upload_to=get_challenge_image_filename,
                                storage=ChallengeStorage(),
                                null=True,
                                blank=True)

    # Processed flag to indicate that participant data has been aggregated and stored.
    # Translators: Whether item has been processed
    end_processed = models.BooleanField(_('processed'), default=False)

    terms = models.ForeignKey(Agreement, related_name='+', blank=False, null=True, on_delete=models.DO_NOTHING)

    prize = models.TextField(_('prize'), blank=True,
                             # Translators: Help text on CMS
                             help_text=_('Prize for winning a challenge.'))

    class Meta:
        # Translators: Collection name on CMS
        verbose_name = _('challenge')

        # Translators: Plural collection name on CMS
        verbose_name_plural = _('challenges')

    def __str__(self):
        return self.name

    def ensure_question_order(self):
        questions = QuizQuestion.objects.filter(challenge=self.pk).order_by('order', 'pk')
        i = 1
        for q in questions:
            q.order = i
            q.save()
            i += 1

    def get_questions(self):
        return QuizQuestion.objects.filter(challenge=self.pk)

    @property
    def is_active(self):
        return (self.state == self.CST_PUBLISHED) and (self.activation_date < timezone.now() < self.deactivation_date)

    def is_active_html(self):
        colour = 'FF0000'
        active = self.is_active
        if active:
            colour = '00FF00'
        return format_html('<span style="color: #{};">{}</span>', colour, str(active))

    is_active_html.admin_order_field = 'state'

    def publish(self):
        self.state = self.CST_PUBLISHED

    @classmethod
    def get_current(cls, user=None):
        """Decides which Challenge the user will receive next."""
        q = Challenge.objects \
            .prefetch_related('participants', 'participants__entries') \
            .order_by('activation_date') \
            .filter(state=cls.CST_PUBLISHED, deactivation_date__gt=timezone.now())

        if user is not None:
            # A participant without entries is incomplete
            q = q.exclude(participants__entries__isnull=False, participants__user__exact=user)

        return q.first()

    def is_participant_a_winner(self, querying_user_id):
        """Checks to see whether or not a participant has been marked as a winner"""
        participant = Participant.objects.get(user_id=querying_user_id)
        if participant is None:
            # How can I move this into the model?
            # participant will be none so I can't call get_winning_status to return the false
            return {"winner": False}
        return participant.get_winning_status

    def view_participants(self):
        return format_html("<a href='/admin/content/participant/?challenge__id__exact="
                           + str(self.id) + "'>" + self.name + "</a> ")


Challenge.panels = [
    wagtail_edit_handlers.MultiFieldPanel(
        [
            wagtail_edit_handlers.FieldPanel('name'),
            wagtail_edit_handlers.FieldPanel('subtitle'),
            wagtail_edit_handlers.FieldPanel('type'),
            wagtail_edit_handlers.FieldPanel('state'),
            wagtail_edit_handlers.FieldPanel('picture'),
            wagtail_edit_handlers.PageChooserPanel('terms'),
            wagtail_edit_handlers.FieldPanel('prize')
        ],
        # Translators: Admin field name
        heading=_('Challenge')
    ),
    wagtail_edit_handlers.MultiFieldPanel(
        [
            wagtail_edit_handlers.FieldPanel('instruction'),
            wagtail_edit_handlers.FieldPanel('call_to_action'),
        ],
        # Translators: Admin field name
        heading=_('Instructional Text')
    ),
    wagtail_edit_handlers.MultiFieldPanel(
        [
            wagtail_edit_handlers.FieldPanel('intro'),
            wagtail_edit_handlers.FieldPanel('outro'),
        ],
        # Translators: Admin field name
        heading=_('Coach UI')
    ),
    wagtail_edit_handlers.MultiFieldPanel(
        [
            wagtail_edit_handlers.FieldPanel('activation_date'),
            wagtail_edit_handlers.FieldPanel('deactivation_date'),
        ],
        # Translators: Admin field name
        heading=_('Dates')
    ),
    wagtail_edit_handlers.InlinePanel(
        'freetext_question',
        [
            wagtail_edit_handlers.FieldPanel('text')
        ],
        # Translators: Admin field name
        label=_('Free Text Question'),
        # Translators: Admin field help
        help_text=_('Only relevant for Freeform type Challenges.')
    ),
    wagtail_edit_handlers.InlinePanel(
        'picture_question',
        [
            wagtail_edit_handlers.FieldPanel('text')
        ],
        # Translators: Admin field name
        label=_('Picture Question'),
        # Translators: Admin field help
        help_text=_('Only relevant for Picture type Challenges.')
    ),
    wagtail_edit_handlers.InlinePanel(
        'questions',
        panels=[
            wagtail_edit_handlers.FieldPanel('text'),
        ],
        # Translators: Admin field name
        label=_('Quiz Questions'),
        # Translators: Admin field help
        help_text=_('Only relevant for Quiz type Challenges.')
    ),
]


@python_2_unicode_compatible
class QuizQuestion(modelcluster_fields.ClusterableModel):
    # Translators: Sorting order
    order = models.PositiveIntegerField(_('order'), default=0)
    challenge = modelcluster_fields.ParentalKey('Challenge', related_name='questions', blank=False, null=True)

    # Translators: Text field
    text = models.TextField(_('text'), blank=True)

    # Translators: Hint text
    hint = models.TextField(_('hint'), blank=True, null=True)

    class Meta:
        # Translators: Collection name on CMS
        verbose_name = _('question')

        # Translators: Plural collection name on CMS
        verbose_name_plural = _('questions')

    def __str__(self):
        return self.text

    def insert_at_order(self, idx):
        questions = QuizQuestion.objects.filter(challenge=self.challenge)
        if questions.count() == 0:
            self.order = 1
            self.save()
        else:
            if idx < 1:
                idx = 1
            if idx > questions.count() + 1:
                self.order = questions.count() + 1
            else:
                if questions[idx - 1] is not None:
                    self.order = idx
                    self.save()
                    while idx <= questions.count():
                        questions[idx].order = idx + 1
                        questions[idx].save()
                        idx += 1

    def get_options(self):
        return QuestionOption.objects.filter(question=self)

    def text_truncated(self):
        return self.text[:75].strip() + '...' if len(self.text) > 75 else self.text

    text_truncated.admin_order_field = 'text'

    @property
    def option_count(self):
        return self.options.all().count()


QuizQuestion.panels = [
    wagtail_edit_handlers.MultiFieldPanel([
        wagtail_edit_handlers.FieldPanel('text'),
        wagtail_edit_handlers.FieldPanel('hint'),
        wagtail_edit_handlers.FieldPanel('challenge'),
        # Translators: Admin field name
    ], heading=_('Question')),
    wagtail_edit_handlers.InlinePanel('options', panels=[
        wagtail_edit_handlers.FieldPanel('text'),
        wagtail_edit_handlers.FieldPanel('correct'),
        # Translators: Admin field name
    ], label=_('Question Options'))
]


@python_2_unicode_compatible
class QuestionOption(models.Model):
    question = modelcluster_fields.ParentalKey('QuizQuestion', related_name='options', blank=False, null=True)

    # Translators: CMS field name
    picture = models.URLField(_('picture URL'), blank=True, null=True)

    # Translators: CMS field name
    text = models.TextField(_('text'), blank=True)

    # Translators: Is this answer a correct one?
    correct = models.BooleanField(_('correct'), default=False)

    class Meta:
        # Translators: Collection name on CMS
        verbose_name = _('question option')

        # Translators: Plural collection name on CMS
        verbose_name_plural = _('question options')

    def __str__(self):
        return self.text


@python_2_unicode_compatible
class PictureQuestion(models.Model):
    challenge = modelcluster_fields.ParentalKey(Challenge, blank=False, null=True, related_name='picture_question',
                                                unique=True)
    text = models.TextField(_('text'), blank=True)

    class Meta:
        # Translators: Collection name on CMS
        verbose_name = _('picture question')

        # Translators: Plural collection name on CMS
        verbose_name_plural = _('picture questions')

    def __str__(self):
        return self.text

    def text_truncated(self):
        return self.text[:75].strip() + '...' if len(self.text) > 75 else self.text


PictureQuestion.panels = [
    wagtail_edit_handlers.MultiFieldPanel(
        [
            wagtail_edit_handlers.FieldPanel('text'),
            wagtail_edit_handlers.FieldPanel('challenge'),
        ],
        # Translators: Admin field name
        heading=_('Picture Questions')
    ),
]


@python_2_unicode_compatible
class FreeTextQuestion(models.Model):
    challenge = modelcluster_fields.ParentalKey(Challenge, blank=False, null=True, related_name='freetext_question',
                                                unique=True)
    text = models.TextField(_('text'), blank=True)

    class Meta:
        # Translators: Collection name on CMS
        verbose_name = _('free text question')

        # Translators: Plural collection name on CMS
        verbose_name_plural = _('free text questions')

    def __str__(self):
        return self.text

    def text_truncated(self):
        return self.text[:75].strip() + '...' if len(self.text) > 75 else self.text


FreeTextQuestion.panels = [
    wagtail_edit_handlers.MultiFieldPanel(
        [
            wagtail_edit_handlers.FieldPanel('challenge'),
            wagtail_edit_handlers.FieldPanel('text'),
        ],
        # Translators: Admin field name
        heading=_('Free Text Questions')
    ),
]


@python_2_unicode_compatible
class Participant(models.Model):
    user = models.ForeignKey(User, related_name='participants', blank=False, null=True)
    challenge = models.ForeignKey(Challenge, related_name='participants', blank=False, null=True)

    # Translators: CMS field name (refers to dates)
    date_created = models.DateTimeField(_('created on'), default=timezone.now)

    # Translators: CMS field name (refers to dates)
    date_completed = models.DateTimeField(_('completed on'), null=True, blank=False)

    # Flag to indicate that participant entry has been 'seen'
    is_read = models.BooleanField(_('is read'), default=False, blank=False)
    is_shortlisted = models.BooleanField(_('is shortlisted'), default=False, blank=False)
    is_winner = models.BooleanField(_('is winner'), default=False, blank=False)

    # Has user received push notification of their winning badge
    has_been_notified = models.BooleanField(_('has_been_notified'), default=False, blank=False)

    badges = models.ManyToManyField('UserBadge')

    @property
    def is_completed(self):
        """A Participant is considered complete when at least one entry has been created."""
        return self.entries.all().exists()

    def mark_is_read(self):
        if self.is_read:
            return format_html("<input type='checkbox' id='{}' class='mark-is-read' value='{}' checked='checked' />",
                               'participant-is-read-%d' % self.id, self.id)
        else:
            return format_html("<input type='checkbox' id='{}' class='mark-is-read' value='{}' />",
                               'participant-is-read-%d' % self.id, self.id)

    def mark_is_shortlisted(self):
        if self.is_shortlisted:
            return format_html(
                "<input type='checkbox' id='{}' class='mark-is-shortlisted' value='{}' checked='checked' />",
                'participant-is-shortlisted-%d' % self.id, self.id)
        else:
            return format_html("<input type='checkbox' id='{}' class='mark-is-shortlisted' value='{}' />",
                               'participant-is-shortlisted-%d' % self.id, self.id)

    def mark_is_winner(self):
        if self.is_winner:
            return format_html("<input type='checkbox' id='{}' class='mark-is-winner' value='{}' checked='checked' />",
                               'participant-is-winner-%d' % self.id, self.id)
        else:
            return format_html("<input type='checkbox' id='{}' class='mark-is-winner' value='{}' />",
                               'participant-is-winner-%d' % self.id, self.id)

    def get_winning_status(self):
        return {"winner": self.is_winner}

    class Meta:
        # Translators: Collection name on CMS
        verbose_name = _('participant')

        # Translators: Plural collection name on CMS
        verbose_name_plural = _('participants')

    def __str__(self):
        return str(self.user) + ": " + str(self.challenge)


Participant.panels = [
    wagtail_edit_handlers.MultiFieldPanel(
        [
            wagtail_edit_handlers.FieldPanel('user'),
            wagtail_edit_handlers.FieldPanel('challenge'),
        ],
        # Translators: Admin field name
        heading=_('Participant')
    ),
    wagtail_edit_handlers.MultiFieldPanel(
        [
            wagtail_edit_handlers.FieldPanel('date_created'),
            wagtail_edit_handlers.FieldPanel('date_completed'),
        ],
        # Translators: Admin field name
        heading=_('Dates')
    ),
    wagtail_edit_handlers.MultiFieldPanel(
        [
            wagtail_edit_handlers.FieldPanel('is_read'),
            wagtail_edit_handlers.FieldPanel('is_shortlisted'),
            wagtail_edit_handlers.FieldPanel('is_winner'),
        ],
        heading=_('Status')
    )
]


@python_2_unicode_compatible
class Entry(models.Model):
    participant = models.ForeignKey(Participant, null=True, related_name='entries')

    # Translators: CMS field name (refers to dates)
    date_saved = models.DateTimeField(_('saved on'), default=timezone.now)

    # Translators: CMS field name (refers to dates)
    date_completed = models.DateTimeField(_('completed on'), null=True)

    class Meta:
        # Translators: Collection name on CMS
        verbose_name = _('entry')

        # Translators: Plural collection name on CMS
        verbose_name_plural = _('entries')

    def __str__(self):
        return str(self.participant.user.username) + ": " + str(self.participant.challenge.name)


@python_2_unicode_compatible
class ParticipantAnswer(models.Model):
    entry = models.ForeignKey(Entry, null=True, related_name='answers')
    question = models.ForeignKey(QuizQuestion, blank=False, null=True, related_name='answers')
    selected_option = models.ForeignKey(QuestionOption, blank=False, null=True, related_name='+')

    # Translators: CMS field name (refers to dates)
    date_answered = models.DateTimeField(_('answered on'))

    # Translators: CMS field name (refers to dates)
    date_saved = models.DateTimeField(_('saved on'), default=timezone.now)

    class Meta:
        # Translators: Collection name on CMS
        verbose_name = _('participant answer')

        # Translators: Plural collection name on CMS
        verbose_name_plural = _('participant answers')

    def __str__(self):
        return str(self.participant.user.username)[:8] + str(self.question.text[:8]) + str(
            self.selected_option.text[:8])


def get_participant_image_filename(instance, filename):
    return '{}-{}'.format(instance.participant.user.pk, filename)


@python_2_unicode_compatible
class ParticipantPicture(models.Model):
    participant = models.ForeignKey(Participant, null=True, related_name='picture_answer')
    question = models.ForeignKey(PictureQuestion, blank=False, null=True, related_name='+')
    picture = models.ImageField(_('picture'),
                                upload_to=get_participant_image_filename,
                                storage=ParticipantPictureStorage(),
                                null=True,
                                blank=True)

    caption = models.CharField(_('caption'), max_length=255, null=True, blank=True)

    # Translators: CMS field name (refers to dates)
    date_answered = models.DateTimeField(_('answered on'), default=timezone.now)

    # Translators: CMS field name (refers to dates)
    date_saved = models.DateTimeField(_('saved on'), default=timezone.now)

    class Meta:
        # Translators: Collection name on CMS
        verbose_name = _('picture answer')

        # Translators: Plural collection name on CMS
        verbose_name_plural = _('picture answers')

    def __str__(self):
        return str(self.user.username)[:8] + ': Pic'


@python_2_unicode_compatible
class ParticipantFreeText(models.Model):
    participant = models.ForeignKey(Participant, null=True, related_name='freetext_answer')
    question = models.ForeignKey(FreeTextQuestion, blank=False, null=True, related_name='+')
    text = models.TextField(_('text'), blank=True)
    date_answered = models.DateTimeField(_('answered on'))
    date_saved = models.DateTimeField(_('saved on'), default=timezone.now)

    class Meta:
        # Translators: Collection name on CMS
        verbose_name = _('free-text answer')

        # Translators: Plural collection name on CMS
        verbose_name_plural = _('free-text answers')

    def __str__(self):
        return str(self.participant) + ': Free'


# ==== #
# Tips #
# ==== #


class TipTag(TaggedItemBase):
    content_object = modelcluster_fields.ParentalKey('content.Tip', related_name='tagged_item')


@python_2_unicode_compatible
class Tip(wagtail_models.Page):
    parent_page_types = ['TipCategory']
    cover_image = models.ForeignKey(wagtail_image_models.Image, blank=True, null=True,
                                    on_delete=models.SET_NULL, related_name='+')

    # Translators: CMS field name
    intro = models.TextField(_('intro dialogue'), blank=True,
                             # Translators: CMS help text
                             help_text=_('The opening line said by the Coach when telling the user about the Tip.'))
    body = wagtail_fields.StreamField([
        ('paragraph', wagtail_blocks.RichTextBlock())
    ])
    tags = ClusterTaggableManager(through=TipTag, blank=True)

    content_panels = wagtail_models.Page.content_panels + [
        wagtail_image_edit.ImageChooserPanel('cover_image'),
        wagtail_edit_handlers.FieldPanel('intro'),
        wagtail_edit_handlers.StreamFieldPanel('body'),
    ]

    promote_panels = wagtail_models.Page.promote_panels + [
        wagtail_edit_handlers.FieldPanel('tags'),
    ]

    class Meta:
        # Translators: Collection name on CMS
        verbose_name = _('tip')

        # Translators: Plural collection name on CMS
        verbose_name_plural = _('tips')

    def get_tag_name_list(self):
        return [tag.name for tag in self.tags.all()]

    def __str__(self):
        return self.title


class TipCategory(wagtail_models.Page):
    parent_page_types = ['TipIndex']
    subpage_types = ['Tip']


class TipIndex(wagtail_models.Page):
    # TODO: When restricting the model to the HomePage, creating a TipIndex excludes a AgreementIndex from being created
    # parent_page_types = ['home.HomePage']
    subpage_types = ['TipCategory']


class TipFavourite(models.Model):
    # Tip Favourite State
    TFST_INACTIVE = 0
    TFST_ACTIVE = 1

    user = models.ForeignKey(User, related_name='+')
    tip = models.ForeignKey(Tip, related_name='favourites', on_delete=models.CASCADE)
    state = models.IntegerField(choices=(
        # Translators: Object state
        (TFST_INACTIVE, _('Disabled')),
        # Translators: Object state
        (TFST_ACTIVE, _('Enabled')),
    ), default=TFST_ACTIVE)
    date_saved = models.DateTimeField(_('saved on'), default=timezone.now)

    class Meta:
        # Translators: Collection name on CMS
        verbose_name = _('tip favourite')

        # Translators: Plural collection name on CMS
        verbose_name_plural = _('tip favourites')

        unique_together = ('user', 'tip')

    @property
    def is_active(self):
        return self.state == self.TFST_ACTIVE

    def favourite(self):
        self.state = self.TFST_ACTIVE

    def unfavourite(self):
        self.state = self.TFST_INACTIVE


def get_goal_image_filename(instance, filename):
    return '/'.join(('goal', str(instance.user.pk), filename))


# ================= #
# Week Calculations #
# ================= #


class WeekCalc:
    @classmethod
    def week_diff(cls, from_date, to_date, rounding):
        if rounding == cls.Rounding.UP:
            return ceil((to_date - from_date).days / 7.0)
        elif rounding == cls.Rounding.DOWN:
            return floor((to_date - from_date).days / 7.0)
        else:
            return (to_date - from_date).days / 7.0

    @classmethod
    def day_diff(cls, from_date, to_date):
        return (to_date - from_date).days

    @classmethod
    def remainder(cls, from_date, to_date):
        """Calculates the remaining days after a week difference has been calculated and rounded down."""
        return cls.day_diff(from_date, to_date) - cls.week_diff(from_date, to_date, cls.Rounding.DOWN) * 7

    class Rounding:
        NONE = 0
        UP = 1
        DOWN = 2


# ===== #
# Goals #
# ===== #


@python_2_unicode_compatible
class GoalPrototype(models.Model):
    INACTIVE = 0
    ACTIVE = 1

    name = models.CharField(max_length=100)
    image = models.ForeignKey(wagtail_image_models.Image, on_delete=models.SET_NULL, related_name='+', null=True)
    state = models.IntegerField(choices=(
        # Translators: Object state
        (INACTIVE, _('Inactive')),
        # Translators: Object state
        (ACTIVE, _('Active')),
    ), default=INACTIVE)
    default_price = models.DecimalField(max_digits=18, decimal_places=2, default=0.0, editable=True)

    @property
    def is_active(self):
        return self.state == GoalPrototype.ACTIVE

    @property
    def num_users(self):
        queryset = Goal.objects.filter(prototype_id=self.id).aggregate(Count('user_id', distinct=True))
        return queryset["user_id__count"]

    def activate(self):
        self.state = GoalPrototype.ACTIVE

    def deactivate(self):
        self.state = GoalPrototype.INACTIVE

    def __str__(self):
        return self.name

    class Meta:
        # Translators: Collection name on CMS
        verbose_name = _('goal prototype')

        # Translators: Plural collection name on CMS
        verbose_name_plural = _('goal prototypes')


GoalPrototype.panels = [
    wagtail_edit_handlers.FieldPanel('name'),
    wagtail_edit_handlers.FieldPanel('state'),
    wagtail_image_edit.ImageChooserPanel('image'),
    wagtail_edit_handlers.FieldPanel('default_price'),
]


@python_2_unicode_compatible
class Goal(models.Model):
    INACTIVE = 0
    ACTIVE = 1

    name = models.CharField(max_length=100)
    start_date = models.DateField()
    end_date = models.DateField()
    original_end_date = models.DateField(blank=True, null=True)
    state = models.IntegerField(choices=(
        # Translators: Object state
        (INACTIVE, _('Inactive')),
        # Translators: Object state
        (ACTIVE, _('Active')),
    ), default=ACTIVE)
    target = models.DecimalField(max_digits=18, decimal_places=2)
    original_target = models.DecimalField(max_digits=18, decimal_places=2, blank=True, null=True)
    weekly_target = models.DecimalField(max_digits=18, decimal_places=2)
    original_weekly_target = models.DecimalField(max_digits=18, decimal_places=2, blank=True, null=True)
    image = models.ImageField(upload_to=get_goal_image_filename, storage=GoalImgStorage(), null=True, blank=True)
    user = models.ForeignKey(User, related_name='+')

    # A null prototype means the Goal is custom
    prototype = models.ForeignKey('GoalPrototype', related_name='goals', on_delete=models.SET_NULL,
                                  default=None, blank=True, null=True)
    end_date_modified = models.DateTimeField(blank=True, null=True)
    target_modified = models.DateTimeField(blank=True, null=True)
    last_edit_date = models.DateTimeField(blank=True, null=True)
    date_deleted = models.DateField(blank=True, null=True)

    class Meta:
        # Translators: Collection name on CMS
        verbose_name = _('goal')

        # Translators: Plural collection name on CMS
        verbose_name_plural = _('goals')

    def save(self, *args, **kwargs):
        # Ensure Weekly Target
        if self.weekly_target is None:
            self.weekly_target = self.get_calculated_weekly_target()
        return super(Goal, self).save(*args, **kwargs)

    def add_new_badge(self, badge):
        if not hasattr(self, '_new_badges'):
            setattr(self, '_new_badges', [])
        self._new_badges.append(badge)

    @property
    def new_badges(self):
        # FIXME: Overriding __init__ causes an exception during a create query.
        if not hasattr(self, '_new_badges'):
            setattr(self, '_new_badges', [])
        return self._new_badges

    def deactivate(self):
        self.date_deleted = timezone.now()
        self.state = Goal.INACTIVE

    @property
    def is_active(self):
        return self.state == Goal.ACTIVE

    @property
    def is_goal_reached(self):
        return self.value >= self.target

    @property
    def is_end_date_modified(self):
        return self.end_date_modified is not None

    @property
    def is_target_modified(self):
        return self.target_modified is not None

    @property
    def progress(self):
        """Returns the progress of the Goal's savings as percentage."""
        return int((self.value / self.target) * 100)

    @property
    def value(self):
        return reduce(lambda acc, el: acc + el['value'],
                      self.transactions.all().order_by('date', 'id').values('value'), 0)

    @property
    def is_custom(self):
        """False if Goal was created from a prototype."""
        return self.prototype is None

    @property
    def weeks(self):
        """The number of weeks from the start date to the end date."""
        return WeekCalc.week_diff(self.start_date, self.end_date, WeekCalc.Rounding.UP) or 1

    @property
    def weeks_to_now(self):
        """Provides the number of weeks from the start date to the current date."""
        return WeekCalc.week_diff(self.start_date, timezone.now().date(), WeekCalc.Rounding.UP)

    @property
    def weeks_left(self):
        """The number of weeks that the Goal has left."""
        return max(WeekCalc.week_diff(timezone.now().date(), self.end_date, WeekCalc.Rounding.UP), 0)

    @property
    def days_left(self):
        """The total number of days the Goal has left."""
        return max(WeekCalc.day_diff(self.end_date, timezone.now().date()), 0)

    @property
    def weekly_average(self):
        """The average savings for the past weeks."""
        weeks_to_now = self.weeks_to_now
        return self.value if weeks_to_now == 0 else ceil(self.value / self.weeks_to_now)

    # @property
    # def weekly_target(self):
    #     """The weekly target for the entire Goal."""
    #     weeks = self.weeks
    #     return self.target if weeks == 0 else ceil(self.target / weeks)

    def get_calculated_weekly_target(self):
        weeks = self.weeks
        return self.target if weeks == 0 else ceil(self.target / weeks)

    @staticmethod
    def _monday(d):
        return d - timedelta(days=d.weekday())

    @staticmethod
    def _date_window(d):
        monday = Goal._monday(d)
        return monday, monday + timedelta(days=6)

    def get_weekly_aggregates(self):
        date = self.start_date

        # Ensure elements so weeks with no transactions will have 0
        agg = [0 for _ in range(self.weeks)]

        week_id = 0
        for trans in self.transactions.all().order_by('date'):
            if WeekCalc.day_diff(date, trans.date.date()) >= 7:
                # Next weekly window
                week_id += 1
                date = (date + timedelta(days=7))

            # Ignore savings after the deadline
            if week_id >= len(agg):
                break

            agg[week_id] += trans.value

        return agg

    @classmethod
    def calculate_weekly_target(cls, start_date, end_date, target):
        weeks = WeekCalc.week_diff(start_date, end_date, WeekCalc.Rounding.UP) or 1
        return target if weeks == 0 else ceil(target / weeks)

    @classmethod
    def get_current_streak(cls, user, now=None, weeks_back=6):
        """Calculates the weekly savings streak for a user, starting at the current time.
        """
        trans_model = apps.get_model('content', 'GoalTransaction')

        now_date = now
        if now is None:
            now_date = timezone.now()

        since_date = now_date - timedelta(weeks=weeks_back)

        trans = trans_model.objects \
            .filter(goal__user=user, date__gt=since_date) \
            .order_by('-date')

        last_monday = Goal._monday(now_date.date())

        # No Transactions at all mean no streak
        streak = 0

        for t in trans:
            monday = Goal._monday(t.date.date())

            if last_monday != monday:
                diff = (last_monday - monday).days
                if diff > 7:
                    # Streak broken
                    break
                else:
                    streak += 1
                    last_monday = monday

        if streak > 0:
            # Any Transactions make for at least 1 week's streak. Weeks are inclusive.
            streak += 1

        return streak

    @classmethod
    def get_current_weekly_target_badge(self, user, goal, now=None, weeks_back=6):
        """Calculates number of weeks in a row that the user has reached the weekly savings target
        """
        trans_model = apps.get_model('content', 'GoalTransaction')

        now_date = now
        if now is None:
            now_date = timezone.now()

        # How far back you check
        since_date = now_date - timedelta(weeks=weeks_back)

        # get all transactions for the specific goal
        transactions = trans_model.objects \
            .filter(goal=goal, date__gt=since_date) \
            .order_by('-date')

        last_monday = Goal._monday(now_date.date())

        # No Transactions at all mean no streak
        streak = 0

        week_savings_total = 0
        broke_out_of_loop = False

        for t in transactions:
            monday = Goal._monday(t.date.date())

            if last_monday != monday:
                # t is now in a different week
                if week_savings_total >= goal.weekly_target:
                    # Streak maintained
                    streak += 1
                    if monday == (last_monday + timedelta(
                            days=-7)):  # This is to check that the user did not stop saving for an entire week
                        last_monday = monday  # move one week back
                        week_savings_total = t.value  # start with the first transaction of this week
                    else:
                        # The user did not save for an entire week and the streak is broken
                        broke_out_of_loop = True
                        break
                else:
                    # Streak broken
                    broke_out_of_loop = True
                    break
            else:
                week_savings_total += t.value

        if not broke_out_of_loop:
            # If you did not break out of the loop the transactions ended and there could be another week in the streak
            # left so we have to check
            if week_savings_total >= goal.weekly_target:
                # Streak maintained
                streak += 1

        return streak

    def is_goal_deadline_missed(self):
        if timezone.now().date() > self.end_date and self.is_active and self.value < self.target:
            return True
        else:
            return False

    def __str__(self):
        return self.name

    class WeekAggregate:
        def __init__(self, id, start_date, end_date, value=0):
            self.id = id
            self.start_date = start_date
            self.end_date = end_date
            self.value = value


@python_2_unicode_compatible
class GoalTransaction(models.Model):
    date = models.DateTimeField(_('date'))
    value = models.DecimalField(_('value'), max_digits=12, decimal_places=2)
    goal = models.ForeignKey(Goal, related_name='transactions')

    class Meta:
        # Translators: Collection name on CMS
        verbose_name = _('goal transaction')

        # Translators: Plural collection name on CMS
        verbose_name_plural = _('goal transactions')

        unique_together = ('date', 'value', 'goal')

    @property
    def is_deposit(self):
        return self.value > 0

    @property
    def is_withdraw(self):
        return self.value <= 0

    def __str__(self):
        return '{} {}'.format(self.date, self.value)


# ============ #
# Achievements #
# ============ #


@python_2_unicode_compatible
class Badge(models.Model):
    INACTIVE = 0
    ACTIVE = 1

    NONE = 0
    GOAL_FIRST_CREATED = 1
    GOAL_HALFWAY = 2
    GOAL_WEEK_LEFT = 3
    GOAL_FIRST_DONE = 4
    TRANSACTION_FIRST = 5
    STREAK_2 = 6
    STREAK_4 = 7
    STREAK_6 = 8
    WEEKLY_TARGET_2 = 9
    WEEKLY_TARGET_4 = 10
    WEEKLY_TARGET_6 = 11
    CHALLENGE_ENTRY = 12
    CHALLENGE_WIN = 13

    BADGE_TYPES = (
        (NONE, _('None')),
        (GOAL_FIRST_CREATED, _('First Goal Created')),
        (GOAL_HALFWAY, _('First Goal Half Way')),
        (GOAL_WEEK_LEFT, _('One Week Left')),
        (GOAL_FIRST_DONE, _('First Goal Done')),
        (TRANSACTION_FIRST, _('First Saving')),
        (STREAK_2, _('2 Week Streak')),
        (STREAK_4, _('4 Week Streak')),
        (STREAK_6, _('6 Week Streak')),
        (WEEKLY_TARGET_2, _('2 Week On Target')),
        (WEEKLY_TARGET_4, _('4 Week On Target')),
        (WEEKLY_TARGET_6, _('6 Week On Target')),
        (CHALLENGE_ENTRY, _('Challenge Participation')),
        (CHALLENGE_WIN, _('Challenge Winner'))
    )

    name = models.CharField(max_length=255)

    badge_type = models.IntegerField(choices=BADGE_TYPES, default=NONE)

    slug = models.SlugField(
        # Translators: CMS field name
        verbose_name=_('slug'),
        allow_unicode=True,
        max_length=255,
        # Translators: Help text on CMS
        help_text=_("The name of the page as it will appear in URLs e.g http://domain.com/blog/[my-slug]/")
    )

    intro = models.TextField(
        # Translators: CMS field name
        _('intro dialogue'),
        # Translators: Help text on CMS
        help_text=_("The opening line said by the Coach when presenting the user with their Badge."),
        blank=True)
    image = models.ForeignKey(wagtail_image_models.Image, blank=True, null=True,
                              on_delete=models.SET_NULL, related_name='+')
    state = models.IntegerField(choices=(
        (INACTIVE, _('Inactive')),
        (ACTIVE, _('Active')),
    ), default=ACTIVE)

    user = models.ManyToManyField(User, through='UserBadge', related_name='badges')

    class Meta:
        # Translators: Collection name on CMS
        verbose_name = _('badge')

        # Translators: Plural collection name on CMS
        verbose_name_plural = _('badges')

    @property
    def is_active(self):
        return self.state == Badge.ACTIVE

    def __str__(self):
        return self.name


Badge.panels = [
    wagtail_edit_handlers.MultiFieldPanel([
        wagtail_edit_handlers.FieldPanel('name'),
        wagtail_edit_handlers.FieldPanel('badge_type'),
        wagtail_edit_handlers.FieldPanel('slug'),
        wagtail_edit_handlers.FieldPanel('state'),
        wagtail_image_edit.ImageChooserPanel('image'),
    ],
        # Translators: Admin field name
        heading=_('Badge')),
    wagtail_edit_handlers.MultiFieldPanel([
        wagtail_edit_handlers.FieldPanel('intro'),
    ],
        # Translators: Admin field name
        heading=_('Coach UI')),
]


@python_2_unicode_compatible
class UserBadge(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    badge = models.ForeignKey(Badge, on_delete=models.CASCADE)
    earned_on = models.DateTimeField(default=timezone.now)

    class Meta:
        # Translators: Collection name on CMS
        verbose_name = _('user badge')

        # Translators: Collection name on CMS
        verbose_name_plural = _('user badges')

    def __str__(self):
        return '{}-{}'.format(self.user, self.badge)


class AchievementStat:
    """Helper object to aggregate User savings achievements."""

    def __init__(self, user):
        self.user = user

        # Streaks
        self.weekly_streak = Goal.get_current_streak(user)

        # User badges
        self.badges = UserBadge.objects.filter(user=user, badge__state=Badge.ACTIVE)

        # User savings inactivity
        self.last_saving_datetime = None
        self.weeks_since_saved = 0

        # TODO: Only consider deposits (transactions of positive values)
        last_trans = GoalTransaction.objects.filter(goal__user=user).order_by('-date').first()
        if last_trans:
            self.last_saving_datetime = last_trans.date
            self.weeks_since_saved = floor((timezone.now() - last_trans.date).days / 7)


def award_first_goal(request, goal):
    """Awarded to users when they create their first Goal."""
    badge_settings = BadgeSettings.for_site(request.site)

    # TODO: Refactor repeated None guards into reusable function
    if badge_settings.goal_first_created is None:
        return None

    if not badge_settings.goal_first_created.is_active:
        return None

    if goal.pk is None:
        raise ValueError(_('Goal instance must be saved before it can be awarded badges.'))

    if Goal.objects.filter(user=goal.user).count() >= 1:
        user_badge, created = UserBadge.objects.get_or_create(user=goal.user, badge=badge_settings.goal_first_created)
        if created:
            return user_badge

    return None


def award_goal_done(request, goal):
    """Awarded to users when they reach their first Goal."""
    badge_settings = BadgeSettings.for_site(request.site)
    badge = badge_settings.goal_first_done

    if badge is None:
        return None

    if not badge.is_active:
        return None

    if goal.pk is None:
        raise ValueError(_('Goal instance must be saved before it can be awarded badges.'))

    if goal.is_goal_reached:
        user_badge, created = UserBadge.objects.get_or_create(user=goal.user, badge=badge)
        if created:
            # Created means it's the first Goal to be completed.
            return user_badge

    return None


def award_goal_halfway(request, goal):
    """Award to users who are halfway to reaching their Goal."""
    badge_settings = BadgeSettings.for_site(request.site)
    badge = badge_settings.goal_half

    if badge is None:
        return None

    if not badge.is_active:
        return None

    if goal.pk is None:
        raise ValueError(_('Goal instance must be saved before it can be awarded badges.'))

    if goal.progress >= 50:
        user_badge, created = UserBadge.objects.get_or_create(user=goal.user, badge=badge)
        if created:
            # Created means it's the first time the user has reached a Goal halfway
            return user_badge


def award_goal_week_left(request, goal):
    badge_settings = BadgeSettings.for_site(request.site)
    badge = badge_settings.goal_week_left

    if badge is None:
        return None

    if not badge.is_active:
        return None

    if goal.pk is None:
        raise ValueError(_('Goal instance must be saved before it can be awarded badges.'))

    # One week left
    if goal.days_left <= 7:
        user_badge, created = UserBadge.objects.get_or_create(user=goal.user, badge=badge)
        if created:
            # Created means it's the first time a user's Goal has reached the week left mark
            return user_badge


def award_transaction_first(request, goal):
    """Award to users who have created their first savings transaction."""
    badge_settings = BadgeSettings.for_site(request.site)
    badge = badge_settings.transaction_first

    if badge is None:
        return None

    if not badge.is_active:
        return None

    if goal.pk is None:
        raise ValueError(_('Goal instance must be saved before it can be awarded badges.'))

    if GoalTransaction.objects.filter(goal__user=goal.user).count() >= 1:
        user_badge, created = UserBadge.objects.get_or_create(user=goal.user, badge=badge)
        if created:
            return user_badge

    return None


def award_week_streak(site, user, weeks):
    """Award to users have saved a number of weeks."""
    badge_settings = BadgeSettings.for_site(site)
    badge = badge_settings.get_streak_badge(weeks)  # Badge is chosen depending on passed in int

    if badge is None:
        return None

    if not badge.is_active:
        return None

    if Goal.get_current_streak(user, timezone.now()) == weeks:
        user_badge, created = UserBadge.objects.get_or_create(user=user, badge=badge)
        if created:
            # Created means it's the first time a user has reached this streak
            return user_badge

    return None


def award_weekly_target_badge(site, user, weeks, goal):
    """Badge Goes to users who have reached their weekly targets for a number of weeks"""
    badge_settings = BadgeSettings.for_site(site)
    badge = badge_settings.get_weekly_target_badge(weeks)  # Badge is chosen depending on passed in int

    if badge is None:
        return None

    if not badge.is_active:
        return None

    if Goal.get_current_weekly_target_badge(user, goal, timezone.now()) == weeks:
        user_badge, created = UserBadge.objects.get_or_create(user=user, badge=badge)
        if created:
            # Created means it's the first time a user has reached this streak
            return user_badge


def award_entry_badge(site, user, participant):
    badge_settings = BadgeSettings.for_site(site)
    badge = badge_settings.challenge_entry

    if badge is None:
        return None

    if not badge.is_active:
        return None

    user_badge, created = participant.badges.get_or_create(user=user, badge=badge)

    if user_badge is not None:
        return user_badge
    else:
        return None


def award_challenge_win(site, user, participant):
    badge_settings = BadgeSettings.for_site(site)
    badge = badge_settings.challenge_win

    if badge is None:
        return None

    if not badge.is_active:
        return None

    if participant.is_winner:
        user_badge, created = participant.badges.get_or_create(user=user, badge=badge)
        return user_badge

    return None


############
# Feedback #
############

@python_2_unicode_compatible
class Feedback(models.Model):
    """Model for feedback left by users. Can be anonymous."""

    # Feedback types
    FT_ASK = 1
    FT_REPORT = 2
    FT_GENERAL = 3
    FT_PARTNER = 4

    # Translators: CMS field
    date_created = models.DateTimeField(_('date created'), default=timezone.now)

    # Translators: CMS field
    is_read = models.BooleanField(_('has been read'), default=False)

    # Translators: CMS field
    text = models.TextField(_('text'), blank=False, null=False)

    type = models.PositiveIntegerField(
        # Translators: CMS field
        _('type'),
        blank=False,
        choices=(
            # Translators: Feedback type
            (FT_ASK, _('Ask a question')),
            # Translators: Feedback type
            (FT_REPORT, _('Report a problem')),
            # Translators: Feedback type
            (FT_GENERAL, _('General feedback')),
            # Translators: Feedback type
            (FT_PARTNER, _('Sponsorship and partnership requests')),
        ),
        null=False
    )

    # Translators: CMS field
    user = modelcluster_fields.ForeignKey(User, null=True)

    class Meta:
        # Translators: Collection name on CMS
        verbose_name = _('feedback entry')

        # Translators: Collection name on CMS
        verbose_name_plural = _('feedback entries')


########################
# Ad Hoc Notification #
########################


class CustomNotification(models.Model):
    message = models.TextField(_('message'), help_text=_('The message shown to the user'), blank=False)
    publish_date = models.DateField(_('publish date'),
                                    help_text=_('The date the notification should start displaying'), blank=False)
    expiration_date = models.DateField(_('end date'),
                                       help_text="The date when the notification should stop displaying")
    icon = models.ForeignKey(wagtail_image_models.Image, on_delete=models.SET_NULL, related_name='+',
                             null=True, blank=True)

    @classmethod
    def get_all_current_notifications(cls):
        """Returns all currently available custom notifications"""
        notifications = CustomNotification.objects.filter(publish_date__lte=timezone.now(),
                                                          expiration_date__gt=timezone.now())

        return notifications


CustomNotification.panels = [
    wagtail_edit_handlers.MultiFieldPanel([
        wagtail_edit_handlers.FieldPanel('message'),
        wagtail_edit_handlers.FieldPanel('publish_date'),
        wagtail_edit_handlers.FieldPanel('expiration_date'),
        wagtail_image_edit.ImageChooserPanel('icon'),
    ],
        # Translators: Admin field name
        heading=_('Custom Notifications')),
]


##########
# Budget #
##########


@python_2_unicode_compatible
class ExpenseCategory(models.Model):
    INACTIVE = 0
    ACTIVE = 1

    name = models.CharField(max_length=100)
    image = models.ForeignKey(wagtail_image_models.Image, on_delete=models.SET_NULL, related_name='+', null=True)
    state = models.IntegerField(choices=(
        # Translators: Object state
        (INACTIVE, _('Inactive')),
        # Translators: Object state
        (ACTIVE, _('Active')),
    ), default=INACTIVE)
    order = models.IntegerField(default=0, help_text=_('The order in which this category will appear on the frontend'))

    class Meta:
        # Translators: Collection name on CMS
        verbose_name = _('expense category')

        # Translators: Plural collection name on CMS
        verbose_name_plural = _('expense categories')

    def __str__(self):
        return self.name


ExpenseCategory.panels = [
    wagtail_edit_handlers.FieldPanel('name'),
    wagtail_edit_handlers.FieldPanel('state'),
    wagtail_image_edit.ImageChooserPanel('image'),
    wagtail_edit_handlers.FieldPanel('order'),
]


@python_2_unicode_compatible
class Budget(modelcluster_fields.ClusterableModel):
    # The user's monthly income
    income = models.DecimalField(_('income'), max_digits=18, decimal_places=2, default=0)

    # The user's monthly savings
    savings = models.DecimalField(_('savings'), max_digits=18, decimal_places=2, default=0)

    user = models.OneToOneField(User, related_name='budget', on_delete=models.CASCADE)

    # Audit

    created_on = models.DateTimeField(default=timezone.now, editable=False)

    class Meta:
        # Translators: Collection name on CMS
        verbose_name = _('budget')

        # Translators: Plural collection name on CMS
        verbose_name_plural = _('budget')

    @property
    def expense(self):
        # Because expenses use a ParentalKey, we get a FakeQuerySet which doesn't have a values() method
        return reduce(lambda acc, value: acc + value,
                      [e.value for e in self.expenses.all().order_by('id')], 0)

    def __str__(self):
        return 'Budget {}'.format(self.user)


Budget.panels = [
    wagtail_edit_handlers.MultiFieldPanel([
        wagtail_edit_handlers.FieldPanel('user'),
        wagtail_edit_handlers.FieldPanel('income'),
        wagtail_edit_handlers.FieldPanel('savings'),
    ],
        # Translators: Admin field name
        heading=_('Budget')),
    wagtail_edit_handlers.InlinePanel(
        'expenses', panels=[
            wagtail_edit_handlers.FieldPanel('name'),
            wagtail_edit_handlers.FieldPanel('value'),
            wagtail_edit_handlers.FieldPanel('category'),
        ],
        # Translators: Admin field name
        label=_('Expenses')),
]


@python_2_unicode_compatible
class Expense(models.Model):
    name = models.CharField(max_length=100, blank=True)

    value = models.DecimalField(_('value'), max_digits=18, decimal_places=2, default=0)

    # A null category means the expense is custom
    category = models.ForeignKey(ExpenseCategory, related_name='+', on_delete=models.SET_NULL,
                                 default=None, blank=True, null=True)

    budget = modelcluster_fields.ParentalKey(Budget, related_name='expenses', on_delete=models.CASCADE,
                                             null=False)

    # Audit

    created_on = models.DateTimeField(default=timezone.now, editable=False)

    class Meta:
        # Translators: Collection name on CMS
        verbose_name = _('expense')

        # Translators: Plural collection name on CMS
        verbose_name_plural = _('expenses')

    @property
    def preferred_name(self):
        if self.name:
            return self.name
        elif self.category:
            return self.category.name
        else:
            # Translators: Default Expense name
            return _('Expense')

    def __str__(self):
        return 'Expense {} {}'.format(self.preferred_name, self.value)
