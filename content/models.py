from django.db import models
from datetime import datetime
from django.utils.encoding import python_2_unicode_compatible


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

    def is_active(self):
        return (self.state == 'published') and (self.activation_date < datetime.now() < self.deactivation_date)


@python_2_unicode_compatible
class Question(models.Model):
    # question types
    QT_CHOICE = 1
    QT_FREEFORM = 2
    QT_PICTURE = 3

    challenge = models.ForeignKey(Challenge, blank=False, null=True)
    picture = models.URLField('Picture URL', blank=False, null=True)
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


@python_2_unicode_compatible
class QuestionOption(models.Model):
    question = models.ForeignKey(Question, blank=False, null=True)
    picture = models.URLField('Picture URL', blank=False, null=True)
    text = models.TextField('Text', blank=True)

    class Meta:
        verbose_name = 'Option'
        verbose_name_plural = 'Options'

    def __str__(self):
        return self.text