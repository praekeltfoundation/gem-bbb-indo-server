
from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from django.utils.encoding import python_2_unicode_compatible
from django.utils.translation import ugettext as _
from modelcluster import fields as modelcluster_fields
from modelcluster.contrib.taggit import ClusterTaggableManager
from taggit.models import TaggedItemBase
from wagtail.wagtailadmin import edit_handlers as wagtail_edit_handlers
from wagtail.wagtailcore import models as wagtail_models
from wagtail.wagtailcore import fields as wagtail_fields
from wagtail.wagtailimages import models as wagtail_image_models
from wagtail.wagtailimages import edit_handlers as wagtail_image_edit

from .storage import GoalImgStorage


@python_2_unicode_compatible
class Challenge(models.Model):
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
    end_processed = models.BooleanField(_('processed'), default=False)

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

    def is_active(self):
        return (self.state == 'published') and (self.activation_date < timezone.now() < self.deactivation_date)


@python_2_unicode_compatible
class QuizQuestion(models.Model):
    order = models.PositiveIntegerField(_('order'), default=0)
    challenge = models.ForeignKey('Challenge', related_name='questions', blank=False, null=True)
    text = models.TextField(_('text'), blank=True)

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


@python_2_unicode_compatible
class QuestionOption(models.Model):
    question = models.ForeignKey('QuizQuestion', related_name='options', blank=False, null=True)
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


@python_2_unicode_compatible
class ParticipantPicture(models.Model):
    participant = models.ForeignKey(Participant, null=True, related_name='picture_answer')
    question = models.ForeignKey(PictureQuestion, blank=False, null=True, related_name='+')
    picture = models.ImageField()
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


class TipTag(TaggedItemBase):
    content_object = modelcluster_fields.ParentalKey('content.Tip', related_name='tagged_item')


@python_2_unicode_compatible
class Tip(wagtail_models.Page):
    cover_image = models.ForeignKey(wagtail_image_models.Image, blank=True, null=True,
                                    on_delete=models.SET_NULL, related_name='+')
    body = wagtail_fields.RichTextField(blank=True)
    tags = ClusterTaggableManager(through=TipTag, blank=True)

    content_panels = wagtail_models.Page.content_panels + [
        wagtail_image_edit.ImageChooserPanel('cover_image'),
        wagtail_edit_handlers.FieldPanel('body'),
    ]

    promote_panels = wagtail_models.Page.promote_panels + [
        wagtail_edit_handlers.FieldPanel('tags'),
    ]

    def get_cover_image_url(self):
        if self.cover_image:
            return self.cover_image.file.url
        else:
            return None

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

    def unfavourite(self):
        self.state = self.TFST_INACTIVE


def get_goal_image_filename(instance, filename):
    return '/'.join(('goal', str(instance.user.pk), filename))


@python_2_unicode_compatible
class Goal(models.Model):
    name = models.CharField(max_length=30)
    start_date = models.DateField()
    end_date = models.DateField()
    value = models.DecimalField(max_digits=12, decimal_places=2)
    image = models.ImageField(upload_to=get_goal_image_filename, storage=GoalImgStorage(), null=True, blank=True)
    user = models.ForeignKey(User, related_name='+')

    class Meta:
        verbose_name = 'goal'
        verbose_name_plural = 'goals'

    def __str__(self):
        return self.name


@python_2_unicode_compatible
class GoalTransaction(models.Model):
    date = models.DateField()
    value = models.DecimalField(max_digits=12, decimal_places=2)
    goal = models.ForeignKey(Goal, related_name='transactions')

    class Meta:
        verbose_name = 'goal transaction'
        verbose_name_plural = 'goal transactions'

    def __str__(self):
        return '{} {}'.format(self.date, self.value)
