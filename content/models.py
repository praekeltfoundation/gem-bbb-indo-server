from django.db import models
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

    name = models.CharField('Challenge Name', max_length=30, null=False, blank=False)
    activation_date = models.DateTimeField('Activate On')
    deactivation_date = models.DateTimeField('Deactivate On')
    # questions = models.ManyToManyField('Questions')
    # challenge_badge = models.ForeignKey('', null=True, blank=True)
    state = models.PositiveIntegerField(
        'State', choices=(
            (CST_INCOMPLETE, 'Incomplete'),
            (CST_REVIEW_READY, 'Ready for review'),
            (CST_PUBLISHED, 'Published'),
            (CST_DONE, 'Done'),
        ),
        default=CST_INCOMPLETE)
    end_processed = models.BooleanField('Processed', default=False)

    class Meta:
        verbose_name = 'Challenge'
        verbose_name_plural = 'Challenges'

    def __str__(self):
        return self.name

    def ensure_question_order(self):
        questions = Question.objects.filter(challenge=self.pk).order_by('order', 'pk')
        i = 1
        for q in questions:
            q.order = i
            q.save()
            i += 1

    def get_questions(self):
        return Question.objects.filter(challenge=self.pk)

    def is_active(self):
        return (self.state == 'published') and (self.activation_date < datetime.now() < self.deactivation_date)


@python_2_unicode_compatible
class Question(models.Model):
    # question types
    QT_CHOICE = 1
    QT_FREEFORM = 2
    QT_PICTURE = 3

    name = models.TextField('Name', blank=True, null=False, unique=True)
    order = models.PositiveIntegerField('Order', default=0)
    challenge = models.ForeignKey(Challenge, related_name='questions', blank=False, null=True)
    picture = models.URLField('Picture URL', blank=True, null=True)
    text = models.TextField('Text', blank=True)
    type = models.PositiveIntegerField(
        'Type', choices=(
            (QT_CHOICE, 'Multiple choice'),
            (QT_FREEFORM, 'Freeform'),
            (QT_PICTURE, 'Picture')
        ),
        default=QT_FREEFORM)

    class Meta:
        verbose_name = 'Question'
        verbose_name_plural = 'Questions'

    def __str__(self):
        return self.text

    def insert_at_order(self, idx):
        questions = Question.objects.filter(challenge=self.challenge)
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
    question = models.ForeignKey(Question, related_name='options', blank=False, null=True)
    next_question = models.ForeignKey(Question, related_name='+', blank=False, null=True)
    picture = models.URLField('Picture URL', blank=True, null=True)
    name = models.TextField('Name', blank=False, null=True)
    text = models.TextField('Text', blank=True)

    class Meta:
        verbose_name = 'Question Option'
        verbose_name_plural = 'Question Options'

    def __str__(self):
        return self.text


@python_2_unicode_compatible
class AnswerLog(models.Model):
    question = models.ForeignKey(Question, blank=False, null=True, related_name='+')
    challenge = models.ForeignKey(Challenge, blank=False, null=True)
    answered = models.DateTimeField('Answered On')
    saved = models.DateTimeField('Saved On',default=timezone.now)
    user = models.TextField('User Id', blank=True)
    response = models.TextField('Response ', blank=True)

    class Meta:
        verbose_name = 'User Answer Log'
        verbose_name_plural = 'User Answers'

    def __str__(self):
        return self.text


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
        verbose_name = 'Tip'
        verbose_name_plural = 'Tips'

    def __str__(self):
        return self.title
