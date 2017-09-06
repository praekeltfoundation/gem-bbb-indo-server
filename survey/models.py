
from collections import namedtuple
from datetime import timedelta
import json

from django.contrib.auth.models import User
from django.core.serializers.json import DjangoJSONEncoder
from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone
from django.utils.html import format_html
from django.utils.six import text_type
from django.utils.text import slugify
from django.utils.translation import ugettext_lazy as _
from wagtail.wagtailcore.models import Page
from wagtail.wagtailadmin.edit_handlers import MultiFieldPanel, InlinePanel
from wagtail.wagtailadmin.edit_handlers import FieldPanel
from modelcluster.fields import ParentalKey
from wagtailsurveys.models import AbstractSurvey, AbstractFormField, AbstractFormSubmission
from unidecode import unidecode

from content.edit_handlers import ReadOnlyPanel


class CoachSurveyIndex(Page):
    subpage_types = ['CoachSurvey']


class CoachSurvey(AbstractSurvey):
    parent_page_types = ['CoachSurveyIndex']
    subpage_types = []

    ANSWER_YES = '1'
    ANSWER_NO = '0'
    CONSENT_KEY = 'survey_consent'

    NONE = 0
    BASELINE = 1
    EATOOL = 2
    ENDLINE = 3
    _REVERSE = {
        'SURVEY_BASELINE': BASELINE,
        'SURVEY_EATOOL': EATOOL,
        'SURVEY_ENDLINE': ENDLINE
    }

    intro = models.TextField(
        # Translators: Field name on CMS
        verbose_name=_('intro dialogue'),
        # Translators: Help text on CMS
        help_text=_("The opening line said by the Coach when introducing the Survey."),
        blank=True, null=False
    )

    outro = models.TextField(
        # Translators: Field name on CMS
        verbose_name=_('outro dialogue'),
        # Translators: Help text on CMS
        help_text=_("The closing line said by the Coach when finishing the Survey."),
        blank=True, null=False
    )

    notification_body = models.TextField(
        # Translators: Field name on CMS
        verbose_name=_('notification body'),
        # Translators: Help text on CMS
        help_text=_("The content body of the first Survey notification the user receives."),
        blank=True, null=False
    )

    reminder_notification_body = models.TextField(
        # Translators: Field name on CMS
        verbose_name=_('reminder notification body'),
        # Translators: Help text on CMS
        help_text=_("The content body of the repeating Survey notifications the user receives."),
        blank=True, null=False
    )

    deliver_after = models.PositiveIntegerField(
        # Translators: Field name on CMS
        verbose_name=_('days to deliver'),
        # Translators: Help text on CMS
        help_text=_("The number of days after user registration that the Survey will be available."),
        default=1
    )

    bot_conversation = models.IntegerField(choices=(
        (NONE, _('none')),
        (BASELINE, _('baseline')),
        (EATOOL, _('ea tool')),
        (ENDLINE, _('endline'))
    ), default=NONE)

    def get_data_fields(self):
        data_fields = [
            ('user_id', _('Unique User ID')),
            ('name', _('Name')),
            ('username', _('Username')),
            ('mobile', _('Mobile Number')),
            ('gender', _('Gender')),
            ('age', _('Age')),
            ('email', _('Email')),
            ('consent', _('Consented to Survey')),
        ]
        data_fields += super(CoachSurvey, self).get_data_fields()

        return data_fields

    def get_form_fields(self):
        return self.form_fields.all()

    def get_submission_class(self):
        return CoachSurveySubmission

    def process_consented_submission(self, consent, form):
        return self.get_submission_class().objects.create(
            form_data=json.dumps(form.cleaned_data, cls=DjangoJSONEncoder),
            page=self, survey=self, user=form.user,
            consent=consent,

            # To preserve historic information
            user_unique_id=form.user.id,
            name=form.user.get_full_name(),
            username=form.user.username,
            mobile=form.user.profile.mobile,
            gender=str(form.user.profile.get_gender_display() if form.user.profile.gender is not None else ""),
            age=str(form.user.profile.age if form.user.profile.age is not None else ""),
            email=form.user.email
        )

    @classmethod
    def get_current(cls, user):
        """
        Returns the current survey a user can complete. Surveys are delivered in the order of their delivery days
        field. If the user has already submitted to a survey, it will no longer be available.

        :param user: The user for checking their submissions and date registered.
        :return:     A tuple containing the survey and its age. Age is measured in days since the survey is first
                     available for the provided user.
        """

        surveys = cls.objects \
            .filter(live=True) \
            .order_by('deliver_after', '-latest_revision_created_at') \
            .exclude(page_ptr__in=CoachSurveySubmission.objects.filter(user=user).values('page'))

        if user.profile:
            surveys = list(filter(lambda s: user.profile.is_joined_days_passed(s.deliver_after), surveys))

        if surveys:
            survey = surveys[0]
            inactivity_age = (timezone.now() - user.date_joined).days - survey.deliver_after
            return survey, inactivity_age

        return None, 0

    @staticmethod
    def get_conversation_type(bot_conversation_name):
        return CoachSurvey._REVERSE.get(bot_conversation_name, None)


CoachSurvey.content_panels = AbstractSurvey.content_panels + [
    MultiFieldPanel(
        [
            FieldPanel('deliver_after'),
            FieldPanel('notification_body'),
            FieldPanel('reminder_notification_body'),
        ],
        # Translators: Admin field name
        heading=_('Push Notifications')
    ),
    MultiFieldPanel(
        [
            FieldPanel('intro'),
            FieldPanel('outro'),
            FieldPanel('bot_conversation'),
        ],
        # Translators: Admin field name
        heading=_('Coach UI')),
    InlinePanel('form_fields', label=_("Form fields")),
]


class CoachFormField(AbstractFormField):
    # Explicit key so that the Label can be changed without breaking submissions
    key = models.CharField(
        _('key'),
        max_length=255,
        help_text=_(
            "Field identifier. Warning: Changing this will prevent existing submissions' fields from being exported."),
        blank=True
    )
    page = ParentalKey(CoachSurvey, related_name='form_fields')

    @property
    def clean_name(self):
        if self.key:
            return self.key
        else:
            return super(CoachFormField, self).clean_name()

    def save(self, *args, **kwargs):
        if self.key:
            self.key = self.slugify(self.key)
        else:
            self.key = super(CoachFormField, self).clean_name
        super(CoachFormField, self).save(*args, **kwargs)

    @staticmethod
    def slugify(name):
        """Taken from `wagtailsurveys.models.AbstractFormField`

        unidecode will return an ascii string while slugify wants a
        unicode string on the other hand, slugify returns a safe-string
        which will be converted to a normal str
        """
        return str(slugify(text_type(unidecode(name))))


CoachFormField.panels = [
                            FieldPanel('key'),
                        ] + CoachFormField.panels


class CoachSurveySubmission(AbstractFormSubmission):
    user = models.ForeignKey(User, on_delete=models.SET_NULL, blank=False, null=True)
    consent = models.BooleanField(default=False)

    # The abstract base class has a `page` field which references the survey, but it has no related name. To find
    # submissions from the survey, we create another foreign key relation. Deleting the survey will delete submission
    # because of the `page` CASCADE option.
    survey = models.ForeignKey(CoachSurvey, on_delete=models.SET_NULL, related_name='submissions', null=True)

    # Fields stored at time of submission, to preserve historic data if the user is deleted
    user_unique_id = models.IntegerField(default=-1)
    name = models.CharField(max_length=100, default='')
    username = models.CharField(max_length=150, default='')
    mobile = models.CharField(max_length=15, default='')
    gender = models.CharField(max_length=10, default='')
    age = models.CharField(max_length=10, default='')
    email = models.CharField(max_length=150, default='')

    def get_data(self):
        form_data = super(CoachSurveySubmission, self).get_data()
        if self.user and self.user.profile:
            # Populate from live user data
            form_data.update({
                'user_id': str(self.user.id),
                'name': self.user.get_full_name(),
                'username': self.user.username,
                'mobile': self.user.profile.mobile,
                'gender': self.user.profile.get_gender_display(),
                'age': str(self.user.profile.age),
                'email': self.user.email,
                'consent': str(self.consent)
            })
        else:
            # Populate from historic user data
            form_data.update({
                'user_id': self.user_unique_id,
                'name': self.name,
                'username': self.username,
                'mobile': self.mobile,
                'gender': self.gender,
                'age': self.age,
                'email': self.email,
                'consent': str(self.consent)
            })

        return form_data


CoachSurveyResponse = namedtuple('CoachSurveyResponse', ['available', 'inactivity_age', 'survey'])


class CoachSurveySubmissionDraft(models.Model):
    """Drafts are to save the user's progress through a survey. As the user answers survey questions, an update is done
    on the appropriate draft.
    """
    user = models.ForeignKey(User)
    survey = models.ForeignKey(CoachSurvey, related_name='drafts')
    consent = models.BooleanField(default=False)
    # Submission is stored as JSON
    submission_data = models.TextField()
    # Submission relation is set when draft is completed.
    submission = models.ForeignKey(CoachSurveySubmission, null=True)
    complete = models.BooleanField(default=False)
    version = models.IntegerField(default=0)
    created_at = models.DateTimeField(default=timezone.now)
    modified_at = models.DateTimeField(default=timezone.now)

    class Meta:
        verbose_name = _('coach survey submission draft')

        verbose_name_plural = _('coach survey submission drafts')

    @property
    def has_submission(self):
        return bool(self.submission_data)

    def save(self, *args, **kwargs):
        self.version += 1
        self.modified_at = timezone.now()
        super(CoachSurveySubmissionDraft, self).save(*args, **kwargs)


###############################
# Endline Survey User Chooser #
###############################


class EndlineSurveySelectUser(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    receive_survey = models.BooleanField(default=False, help_text=_('Should the user receive the Endline Survey'))
    survey_completed = models.BooleanField(default=False, help_text=_('Has the user already completed the survey'))

    class Meta:
        # Translators: Collection name on CMS
        verbose_name = _('endline survey selected user')

        # Translators: Plural collection name on CMS
        verbose_name_plural = _('endline survey selected users')

    def receive_endline_survey(self):
        if self.receive_survey:
            return format_html(
                "<input type='checkbox' id='{}' class='mark-receive-survey' value='{}' checked='checked' />",
                'participant-is-shortlisted-%d' % self.id, self.id)
        else:
            return format_html("<input type='checkbox' id='{}' class='mark-receive-survey' value='{}' />",
                               'participant-is-shortlisted-%d' % self.id, self.id)

    @property
    def is_baseline_completed(self):
        baseline_surveys = CoachSurvey.objects.filter(bot_conversation=CoachSurvey.BASELINE).first()
        completed = CoachSurveySubmission.objects.filter(survey=baseline_surveys, user=self.user).first()

        if not completed:
            return False
        return True

    @property
    def is_endline_completed(self):
        endline_surveys = CoachSurvey.objects.filter(bot_conversation=CoachSurvey.ENDLINE).first()
        completed = CoachSurveySubmission.objects.filter(survey=endline_surveys, user=self.user).first()

        if not completed:
            return False
        return True

EndlineSurveySelectUser.panels = [
    MultiFieldPanel([
        FieldPanel('user'),
        FieldPanel('receive_survey'),
        ReadOnlyPanel('is_baseline_completed'),
        ReadOnlyPanel('is_endline_completed',)
    ])
]


@receiver(post_save, sender=User)
def create_survey_link(sender, instance, created, **kwargs):
    if created:
        EndlineSurveySelectUser.objects.get_or_create(user=instance)
