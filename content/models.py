from django.db import models
from datetime import datetime


# Create your models here.
class Challenge(models.Model):
    # challenge states
    CST_INCOMPLETE = 0
    CST_REVIEW_READY = 1
    CST_PUBLISHED = 2
    CST_DONE = 3

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

    def __str__(self):
        return self.name

    def is_active(self):
        return (self.state == 'published') and (self.activation_date < datetime.now() < self.deactivation_date)