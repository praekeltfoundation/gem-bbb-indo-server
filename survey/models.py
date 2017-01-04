
import json

from django.contrib.auth.models import User
from django.core.serializers.json import DjangoJSONEncoder
from django.db import models
from django.utils.translation import ugettext_lazy as _
from wagtail.wagtailcore.models import Page
from wagtail.wagtailadmin.edit_handlers import MultiFieldPanel, InlinePanel
from wagtail.wagtailadmin.edit_handlers import FieldPanel
from modelcluster.fields import ParentalKey
from wagtailsurveys.models import AbstractSurvey, AbstractFormField, AbstractFormSubmission


class CoachSurvey(AbstractSurvey):
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

    deliver_after = models.PositiveIntegerField(
        # Translators: Field name on CMS
        verbose_name=_('days to deliver'),
        # Translators: Help text on CMS
        help_text=_("The number of days after user registration that the Survey will be available."),
        default=1
    )

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


CoachSurvey.content_panels = AbstractSurvey.content_panels + [
    MultiFieldPanel(
        [
            FieldPanel('deliver_after')
        ],
        # Translators: Admin field name
        heading=_('Survey')
    ),
    MultiFieldPanel(
        [
            FieldPanel('intro'),
            FieldPanel('outro'),
        ],
        # Translators: Admin field name
        heading=_('Coach UI')),
    InlinePanel('form_fields', label=_("Form fields")),
]


class CoachFormField(AbstractFormField):
    page = ParentalKey(CoachSurvey, related_name='form_fields')


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
