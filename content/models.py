
from uuid import uuid4
from collections import OrderedDict
from datetime import timedelta
from functools import reduce
from math import ceil
from os.path import splitext

from django.apps import apps
from django.contrib.auth.models import User
from django.db import models
from django.utils import timezone
from django.utils.encoding import python_2_unicode_compatible
from django.utils.translation import ugettext as _
from modelcluster import fields as modelcluster_fields
from modelcluster.contrib.taggit import ClusterTaggableManager
from taggit.models import TaggedItemBase
from wagtail.wagtailadmin import edit_handlers as wagtail_edit_handlers
from wagtail.wagtailcore import fields as wagtail_fields
from wagtail.wagtailcore import models as wagtail_models
from wagtail.wagtailcore import blocks as wagtail_blocks
from wagtail.wagtailimages import edit_handlers as wagtail_image_edit
from wagtail.wagtailimages import models as wagtail_image_models

from .storage import ChallengeStorage, GoalImgStorage, ParticipantPictureStorage


# ========== #
# Agreements #
# ========== #


class Agreement(wagtail_models.Page):
    body = wagtail_fields.RichTextField(blank=True)

    content_panels = wagtail_models.Page.content_panels + [
        wagtail_edit_handlers.FieldPanel('body')
    ]

    class Meta:
        verbose_name = _('agreement')
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

    name = models.CharField(_('challenge name'), max_length=30, null=False, blank=False)
    activation_date = models.DateTimeField(_('activate on'))
    deactivation_date = models.DateTimeField(_('deactivate on'))
    # questions = models.ManyToManyField('Questions')
    # challenge_badge = models.ForeignKey('', null=True, blank=True)
    state = models.PositiveIntegerField(
        'state', choices=(
            (CST_INCOMPLETE, _('Incomplete')),
            (CST_REVIEW_READY, _('Ready for review')),
            (CST_PUBLISHED, _('Published')),
            (CST_DONE, _('Done')),
        ),
        default=CST_INCOMPLETE)
    type = models.PositiveIntegerField(
        'type', choices=(
            (CTP_QUIZ, _('Quiz')),
            (CTP_PICTURE, _('Picture')),
            (CTP_FREEFORM, _('Free text')),
        ),
        default=CTP_QUIZ)
    picture = models.ImageField(_('picture'),
                                upload_to=get_challenge_image_filename,
                                storage=ChallengeStorage(),
                                null=True,
                                blank=True)
    end_processed = models.BooleanField(_('processed'), default=False)

    agreement = models.ManyToManyField(Agreement, through='ChallengeAgreement')

    class Meta:
        verbose_name = _('challenge')
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

    def publish(self):
        self.state = self.CST_PUBLISHED


Challenge.panels = [
    wagtail_edit_handlers.MultiFieldPanel([
        wagtail_edit_handlers.FieldPanel('name'),
        wagtail_edit_handlers.FieldPanel('type'),
        wagtail_edit_handlers.FieldPanel('state'),
        wagtail_edit_handlers.FieldPanel('picture'),
    ], heading=_('Challenge')),
    wagtail_edit_handlers.MultiFieldPanel([
        wagtail_edit_handlers.FieldPanel('activation_date'),
        wagtail_edit_handlers.FieldPanel('deactivation_date'),
    ], heading=_('Dates')),
    wagtail_edit_handlers.InlinePanel('questions', panels=[
        wagtail_edit_handlers.FieldPanel('text'),
        wagtail_edit_handlers.FieldPanel('hint'),
    ], label=_('Questions')),
]


class ChallengeAgreement(models.Model):
    challenge = models.ForeignKey(Challenge, on_delete=models.CASCADE)
    agreement = models.ForeignKey(Agreement, on_delete=models.CASCADE)


@python_2_unicode_compatible
class QuizQuestion(modelcluster_fields.ClusterableModel):
    order = models.PositiveIntegerField(_('order'), default=0)
    challenge = modelcluster_fields.ParentalKey('Challenge', related_name='questions', blank=False, null=True)
    text = models.TextField(_('text'), blank=True)
    hint = models.TextField(_('hint'), blank=True, null=True)

    class Meta:
        verbose_name = _('question')
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


QuizQuestion.panels = [
    wagtail_edit_handlers.MultiFieldPanel([
        wagtail_edit_handlers.FieldPanel('text'),
        wagtail_edit_handlers.FieldPanel('hint'),
        wagtail_edit_handlers.FieldPanel('challenge'),
    ], heading=_('Question')),
    wagtail_edit_handlers.InlinePanel('options', panels=[
        wagtail_edit_handlers.FieldPanel('text'),
        wagtail_edit_handlers.FieldPanel('correct'),
    ], label=_('Question Options'))
]


@python_2_unicode_compatible
class QuestionOption(models.Model):
    question = modelcluster_fields.ParentalKey('QuizQuestion', related_name='options', blank=False, null=True)
    picture = models.URLField(_('picture URL'), blank=True, null=True)
    text = models.TextField(_('text'), blank=True)
    correct = models.BooleanField(_('correct'), default=False)

    class Meta:
        verbose_name = _('question option')
        verbose_name_plural = _('question options')

    def __str__(self):
        return self.text


@python_2_unicode_compatible
class PictureQuestion(models.Model):
    challenge = models.OneToOneField(Challenge, related_name='picture_question', blank=False, null=True)
    text = models.TextField(_('text'), blank=True)

    class Meta:
        verbose_name = _('picture question')
        verbose_name_plural = _('picture questions')

    def __str__(self):
        return self.text


@python_2_unicode_compatible
class FreeTextQuestion(models.Model):
    challenge = models.OneToOneField(Challenge, related_name='freetext_question', blank=False, null=True)
    text = models.TextField(_('text'), blank=True)

    class Meta:
        verbose_name = _('free text question')
        verbose_name_plural = _('free text questions')

    def __str__(self):
        return self.text


@python_2_unicode_compatible
class Participant(models.Model):
    user = models.ForeignKey(User, related_name='users', blank=False, null=True)
    challenge = models.ForeignKey(Challenge, related_name='challenges', blank=False, null=True)
    completed = models.BooleanField(_('completed'), default=False)
    date_created = models.DateTimeField(_('created on'), default=timezone.now)
    date_completed = models.DateTimeField(_('completed on'), null=True)

    class Meta:
        verbose_name = _('participant')
        verbose_name_plural = _('participants')

    def __str__(self):
        return str(self.user) + ": " + str(self.challenge)


@python_2_unicode_compatible
class Entry(models.Model):
    participant = models.ForeignKey(Participant, null=True, related_name='entries')
    date_saved = models.DateTimeField(_('saved on'), default=timezone.now)
    date_completed = models.DateTimeField(_('completed on'), null=True)

    class Meta:
        verbose_name = _('entry')
        verbose_name_plural = _('entries')

    def __str__(self):
        return str(self.participant.user.username) + ": " + str(self.participant.challenge.name)


@python_2_unicode_compatible
class ParticipantAnswer(models.Model):
    entry = models.ForeignKey(Entry, null=True, related_name='answers')
    question = models.ForeignKey(QuizQuestion, blank=False, null=True, related_name='+')
    selected_option = models.ForeignKey(QuestionOption, blank=False, null=True, related_name='+')
    date_answered = models.DateTimeField(_('answered on'))
    date_saved = models.DateTimeField(_('saved on'), default=timezone.now)

    class Meta:
        verbose_name = _('participant answer')
        verbose_name_plural = _('participant answers')

    def __str__(self):
        return str(self.participant.user.username)[:8] + str(self.question.text[:8]) + str(self.selected_option.text[:8])


def get_participant_image_filename(instance, filename):
    return '{}-{}'.format(instance.user.pk, filename)


@python_2_unicode_compatible
class ParticipantPicture(models.Model):
    participant = models.ForeignKey(Participant, null=True, related_name='picture_answer')
    question = models.ForeignKey(PictureQuestion, blank=False, null=True, related_name='+')
    picture = models.ImageField(_('picture'),
                                upload_to=get_participant_image_filename,
                                storage=ParticipantPictureStorage(),
                                null=True,
                                blank=True)
    date_answered = models.DateTimeField(_('answered on'))
    date_saved = models.DateTimeField(_('saved on'), default=timezone.now)

    class Meta:
        verbose_name = _('picture answer')
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
        verbose_name = _('free-text answer')
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
    intro = models.CharField(_('intro dialogue'), max_length=200, blank=True,
                             help_text=_('The opening line said by the Coach when telling the user about the Tip'))
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
        verbose_name = _('tip')
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
        (TFST_INACTIVE, _('Disabled')),
        (TFST_ACTIVE, _('Enabled')),
    ), default=TFST_ACTIVE)
    date_saved = models.DateTimeField(_('saved on'), default=timezone.now)

    class Meta:
        verbose_name = _('tip favourite')
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
class Goal(models.Model):
    name = models.CharField(max_length=30)
    start_date = models.DateField()
    end_date = models.DateField()
    target = models.DecimalField(max_digits=18, decimal_places=2)
    image = models.ImageField(upload_to=get_goal_image_filename, storage=GoalImgStorage(), null=True, blank=True)
    user = models.ForeignKey(User, related_name='+')

    @property
    def value(self):
        return reduce(lambda acc, el: acc+el['value'],
                      self.transactions.all().order_by('date', 'id').values('value'), 0)

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

    class Meta:
        verbose_name = _('goal')
        verbose_name_plural = _('goals')

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
    date = models.DateTimeField()
    value = models.DecimalField(max_digits=12, decimal_places=2)
    goal = models.ForeignKey(Goal, related_name='transactions')

    class Meta:
        verbose_name = _('goal transaction')
        verbose_name_plural = _('goal transactions')
        unique_together = ('date', 'value', 'goal')

    def __str__(self):
        return '{} {}'.format(self.date, self.value)
