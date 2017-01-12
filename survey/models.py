
from collections import namedtuple
from datetime import timedelta
import json

from django.contrib.auth.models import User
from django.core.serializers.json import DjangoJSONEncoder
from django.db import models
from django.utils import timezone
from django.utils.six import text_type
from django.utils.text import slugify
from django.utils.translation import ugettext_lazy as _
from wagtail.wagtailcore.models import Page
from wagtail.wagtailadmin.edit_handlers import MultiFieldPanel, InlinePanel
from wagtail.wagtailadmin.edit_handlers import FieldPanel
from modelcluster.fields import ParentalKey
from wagtailsurveys.models import AbstractSurvey, AbstractFormField, AbstractFormSubmission
from unidecode import unidecode


class CoachSurvey(AbstractSurvey):
    NONE = 0
    BASELINE = 1
    EATOOL = 2

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
    ), default=NONE)

    def get_data_fields(self):
        data_fields = [
            ('name', _('Name')),
            ('username', _('Username')),
            ('mobile', _('Mobile Number')),
            ('email', _('Email')),
        ]
        data_fields += super(CoachSurvey, self).get_data_fields()

        return data_fields

    def get_form_fields(self):
        return self.form_fields.all()

    def get_submission_class(self):
        return CoachSurveySubmission

    def process_form_submission(self, form):
        self.get_submission_class().objects.create(
            form_data=json.dumps(form.cleaned_data, cls=DjangoJSONEncoder),
            page=self, user=form.user,

            # To preserve historic information
            name=form.user.get_full_name(),
            username=form.user.username,
            mobile=form.user.profile.mobile,
            email=form.user.email
        )

    @classmethod
    def get_current(cls, user):

        surveys = cls.objects \
            .filter(live=True) \
            .order_by('deliver_after', '-latest_revision_created_at') \
            .exclude(page_ptr__in=CoachSurveySubmission.objects.filter(user=user).values('page'))

        if user.profile:
            surveys = list(filter(lambda s: user.profile.is_joined_days_passed(s.deliver_after), surveys))

        if surveys:
            return surveys[0]

        return None


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

    # Fields stored at time of submission, to preserve historic data if the user is deleted
    name = models.CharField(max_length=100, default='')
    username = models.CharField(max_length=150, default='')
    mobile = models.CharField(max_length=15, default='')
    email = models.CharField(max_length=150, default='')

    def get_data(self):
        form_data = super(CoachSurveySubmission, self).get_data()
        if self.user and self.user.profile:
            # Populate from live user data
            form_data.update({
                'name': self.user.get_full_name(),
                'username': self.user.username,
                'mobile': self.user.profile.mobile,
                'email': self.user.email
            })
        else:
            # Populate from historic user data
            form_data.update({
                'name': self.name,
                'username': self.username,
                'mobile': self.mobile,
                'email': self.email
            })

        return form_data


CoachSurveyResponse = namedtuple('CoachSurveyResponse', ['available', 'survey'])