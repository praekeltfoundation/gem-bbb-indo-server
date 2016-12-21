from uuid import uuid4
from collections import OrderedDict
from datetime import timedelta
from functools import reduce
from math import ceil
from os.path import splitext

from django.apps import apps
from django.utils.html import format_html
from django.contrib.auth.models import User
from django.db import models
from django.utils import timezone
from django.utils.encoding import python_2_unicode_compatible
from django.utils.translation import ugettext as _
from modelcluster import fields as modelcluster_fields
from modelcluster.contrib.taggit import ClusterTaggableManager
from taggit.models import TaggedItemBase
from wagtail.contrib.settings.models import BaseSetting, register_setting
from wagtail.wagtailadmin import edit_handlers as wagtail_edit_handlers
from wagtail.wagtailsnippets.models import register_snippet
from wagtail.wagtailsnippets import edit_handlers as wagtail_snippet_edit_handlers
from wagtail.wagtailcore import fields as wagtail_fields
from wagtail.wagtailcore import models as wagtail_models
from wagtail.wagtailcore import blocks as wagtail_blocks
from wagtail.wagtailimages import edit_handlers as wagtail_image_edit
from wagtail.wagtailimages import models as wagtail_image_models

from .storage import ChallengeStorage, GoalImgStorage, ParticipantPictureStorage


# ======== #
# Settings #
# ======== #


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


BadgeSettings.panels = [
    wagtail_edit_handlers.MultiFieldPanel([
        wagtail_edit_handlers.FieldPanel('goal_first_created'),
        wagtail_edit_handlers.FieldPanel('goal_half'),
        wagtail_edit_handlers.FieldPanel('goal_week_left'),
        wagtail_edit_handlers.FieldPanel('goal_first_done'),
        wagtail_edit_handlers.FieldPanel('transaction_first'),
    ],
        # Translators: Admin field name
        heading=_("Badge types"))
]


# ========== #
# Agreements #
# ========== #


class Agreement(wagtail_models.Page):
    body = wagtail_fields.RichTextField(blank=True)

    content_panels = wagtail_models.Page.content_panels + [
        wagtail_edit_handlers.FieldPanel('body')
    ]

    class Meta:
        # Translators: Collection name on CMS
        verbose_name = _('agreement')

        # Translators: Plural collection name on CMS
        verbose_name_plural = _('agreements')


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


Challenge.panels = [
    wagtail_edit_handlers.MultiFieldPanel(
        [
            wagtail_edit_handlers.FieldPanel('name'),
            wagtail_edit_handlers.FieldPanel('subtitle'),
            wagtail_edit_handlers.FieldPanel('type'),
            wagtail_edit_handlers.FieldPanel('state'),
            wagtail_edit_handlers.FieldPanel('picture'),
            wagtail_edit_handlers.PageChooserPanel('terms')
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
    user = models.ForeignKey(User, related_name='users', blank=False, null=True)
    challenge = models.ForeignKey(Challenge, related_name='participants', blank=False, null=True)

    # Translators: CMS field name (refers to dates)
    date_created = models.DateTimeField(_('created on'), default=timezone.now)

    # Translators: CMS field name (refers to dates)
    date_completed = models.DateTimeField(_('completed on'), null=True)

    @property
    def is_completed(self):
        """A Participant is considered complete when at least one entry has been created."""
        return self.entries.all().exists()

    class Meta:
        # Translators: Collection name on CMS
        verbose_name = _('participant')

        # Translators: Plural collection name on CMS
        verbose_name_plural = _('participants')

    def __str__(self):
        return str(self.user) + ": " + str(self.challenge)


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
    question = models.ForeignKey(QuizQuestion, blank=False, null=True, related_name='+')
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

    def get_tag_name_list(self):
        return [tag.name for tag in self.tags.all()]

    class Meta:
        # Translators: Collection name on CMS
        verbose_name = _('tip')

        # Translators: Plural collection name on CMS
        verbose_name_plural = _('tips')

    def __str__(self):
        return self.title


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

    def get_user_count(self):
        """The number of users that have created Goals using this prototype."""
        # TODO
        return 0

    @property
    def is_active(self):
        return self.state == GoalPrototype.ACTIVE

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
]


@python_2_unicode_compatible
class Goal(models.Model):
    INACTIVE = 0
    ACTIVE = 1

    name = models.CharField(max_length=100)
    start_date = models.DateField()
    end_date = models.DateField()
    state = models.IntegerField(choices=(
        # Translators: Object state
        (INACTIVE, _('Inactive')),
        # Translators: Object state
        (ACTIVE, _('Active')),
    ), default=ACTIVE)
    target = models.DecimalField(max_digits=18, decimal_places=2)
    image = models.ImageField(upload_to=get_goal_image_filename, storage=GoalImgStorage(), null=True, blank=True)
    user = models.ForeignKey(User, related_name='+')
    prototype = models.ForeignKey('GoalPrototype', related_name='goals', on_delete=models.SET_NULL,
                                  default=None, blank=True, null=True)

    class Meta:
        # Translators: Collection name on CMS
        verbose_name = _('goal')

        # Translators: Plural collection name on CMS
        verbose_name_plural = _('goals')

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
        self.state = Goal.INACTIVE

    @property
    def is_active(self):
        return self.state == Goal.ACTIVE

    @property
    def is_goal_reached(self):
        return self.value >= self.target

    @property
    def value(self):
        return reduce(lambda acc, el: acc + el['value'],
                      self.transactions.all().order_by('date', 'id').values('value'), 0)

    @property
    def is_custom(self):
        """False if Goal was created from a prototype."""
        return self.prototype is None

    @property
    def week_count(self):
        monday1 = Goal._monday(self.start_date)
        monday2 = Goal._monday(self.end_date)

        # Weeks are inclusive, so 1 is added
        return int(((monday2 - monday1).days / 7) + 1)

    @property
    def week_count_to_now(self):
        """Provides the number of weeks from the start date to the current date."""
        monday1 = Goal._monday(self.start_date)
        monday2 = Goal._monday(timezone.now().date())
        return int(((monday2 - monday1).days / 7) + 1)

    @property
    def weekly_average(self):
        return ceil(self.value / self.week_count_to_now)

    @property
    def weekly_target(self):
        return ceil(self.target / self.week_count)

    @staticmethod
    def _monday(d):
        return d - timedelta(days=d.weekday())

    @staticmethod
    def _date_window(d):
        monday = Goal._monday(d)
        return monday, monday + timedelta(days=6)

    def get_weekly_aggregates(self):
        monday, sunday = self._date_window(self.start_date)
        agg = OrderedDict()
        week_id = 1
        agg[monday] = self.WeekAggregate(week_id, monday, sunday)

        while sunday <= self.end_date:
            week_id += 1
            monday, sunday = self._date_window(sunday + timedelta(days=1))
            agg[monday] = self.WeekAggregate(week_id, monday, sunday)

        for t in self.transactions.all():
            monday = Goal._monday(t.date.date())
            if monday in agg:
                agg[monday].value += t.value

        return [v for k, v in agg.items()]

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

    name = models.CharField(max_length=255)
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
    wagtail_edit_handlers.FieldPanel('name'),
    wagtail_edit_handlers.FieldPanel('state'),
    wagtail_image_edit.ImageChooserPanel('image'),
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

        unique_together = ('user', 'badge')

    def __str__(self):
        return '{}-{}'.format(self.user, self.badge)


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

    if Goal.objects.filter(user=goal.user).count() == 1:
        user_badge, created = UserBadge.objects.get_or_create(user=goal.user, badge=badge_settings.goal_first_created)
        return user_badge
    else:
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
    pass


def award_goal_week_left(request, goal):
    pass


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

    if GoalTransaction.objects.filter(goal__user=goal.user).count() == 1:
        user_badge, created = UserBadge.objects.get_or_create(user=goal.user, badge=badge)
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
            (FT_ASK,        _('Ask a question')),
            # Translators: Feedback type
            (FT_REPORT,     _('Report a problem')),
            # Translators: Feedback type
            (FT_GENERAL,    _('General feedback')),
            # Translators: Feedback type
            (FT_PARTNER,    _('Sponsorship and partnership requests')),
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

