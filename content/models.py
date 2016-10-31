from django.db import models
from django.contrib.auth.models import User
from datetime import datetime
from django.utils.encoding import python_2_unicode_compatible
from django.utils import timezone
from modelcluster import fields as modelcluster_fields
from modelcluster.contrib.taggit import ClusterTaggableManager
from taggit.models import TaggedItemBase
from wagtail.wagtailadmin import edit_handlers as wagtail_edit_handlers
from wagtail.wagtailcore import models as wagtail_models
from wagtail.wagtailcore import fields as wagtail_fields
from wagtail.wagtailimages import models as wagtail_image_models
from wagtail.wagtailimages import edit_handlers as wagtail_image_edit


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

    name = models.CharField('challenge name', max_length=30, null=False, blank=False)
    activation_date = models.DateTimeField('activate on')
    deactivation_date = models.DateTimeField('deactivate on')
    # questions = models.ManyToManyField('Questions')
    # challenge_badge = models.ForeignKey('', null=True, blank=True)
    state = models.PositiveIntegerField(
        'state', choices=(
            (CST_INCOMPLETE, 'Incomplete'),
            (CST_REVIEW_READY, 'Ready for review'),
            (CST_PUBLISHED, 'Published'),
            (CST_DONE, 'Done'),
        ),
        default=CST_INCOMPLETE)
    type = models.PositiveIntegerField(
        'type', choices=(
            (CTP_QUIZ, 'Quiz'),
            (CTP_PICTURE, 'Picture'),
            (CTP_FREEFORM, 'Free text'),
        ),
        default=CTP_QUIZ)
    end_processed = models.BooleanField('processed', default=False)

    class Meta:
        verbose_name = 'challenge'
        verbose_name_plural = 'challenges'

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
        return (self.state == 'published') and (self.activation_date < datetime.now() < self.deactivation_date)


@python_2_unicode_compatible
class QuizQuestion(models.Model):
    order = models.PositiveIntegerField('order', default=0)
    challenge = models.ForeignKey('Challenge', related_name='questions', blank=False, null=True)
    text = models.TextField('text', blank=True)

    class Meta:
        verbose_name = 'question'
        verbose_name_plural = 'questions'

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
    picture = models.URLField('picture URL', blank=True, null=True)
    text = models.TextField('text', blank=True)
    correct = models.BooleanField('correct', default=False)

    class Meta:
        verbose_name = 'question option'
        verbose_name_plural = 'question options'

    def __str__(self):
        return self.text


@python_2_unicode_compatible
class Participant(models.Model):
    user = models.ForeignKey(User, related_name='users', blank=False, null=True)
    challenge = models.ForeignKey(Challenge, related_name='challenges', blank=False, null=True)
    completed = models.BooleanField('completed', default=False)
    date_created = models.DateTimeField('created on', default=datetime.now)
    date_completed = models.DateTimeField('completed on', null=True)

    class Meta:
        verbose_name = 'participant'
        verbose_name_plural = 'participants'

    def __str__(self):
        return str(self.user) + ": " + str(self.challenge)


@python_2_unicode_compatible
class ParticipantAnswer(models.Model):
    participant = models.ForeignKey(Participant, null=True, related_name='answers')
    question = models.ForeignKey(QuizQuestion, blank=False, null=True, related_name='+')
    selected_option = models.ForeignKey(QuestionOption, blank=False, null=True, related_name='+')
    date_answered = models.DateTimeField('answered on')
    date_saved = models.DateTimeField('saved on', default=datetime.now)

    class Meta:
        verbose_name = 'participant answer'
        verbose_name_plural = 'participant answers'

    def __str__(self):
        return str(self.user.username)[:8] + str(self.question.text[:8]) + str(self.selected_option.text[:8])


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
        verbose_name = 'tip'
        verbose_name_plural = 'tips'

    def __str__(self):
        return self.title
