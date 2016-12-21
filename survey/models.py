
from django.db import models
from django.utils.translation import ugettext_lazy as _
from wagtail.wagtailcore.models import Page
from wagtail.wagtailadmin.edit_handlers import MultiFieldPanel, InlinePanel
from wagtail.wagtailadmin.edit_handlers import FieldPanel
from modelcluster.fields import ParentalKey
from wagtailsurveys.models import AbstractSurvey, AbstractFormField


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

    def get_form_fields(self):
        return self.custom_form_fields.all()


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
    InlinePanel('custom_form_fields', label=_("Form fields")),
]


class CoachFormField(AbstractFormField):
    page = ParentalKey(CoachSurvey, related_name='custom_form_fields')
