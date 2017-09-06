from django.conf.urls import url, include
from wagtail.contrib.modeladmin.options import ModelAdmin, ModelAdminGroup, modeladmin_register
from wagtail.wagtailcore import hooks
from django.utils.translation import ugettext_lazy as _

from .models import EndlineSurveySelectUser
from . import admin_urls


# ======= #
# Surveys #
# ======= #


class EndlineUserAdmin(ModelAdmin):
    model = EndlineSurveySelectUser
    index_view_extra_js = ['js/js.cookie.js', 'js/endline_survey.js']
    list_display = ('user', 'is_baseline_completed', 'is_endline_completed', 'receive_endline_survey',)
    search_fields = ('user',)
    list_filter = ('receive_survey', 'survey_completed',)
    menu_label = _('Endline Survey')
    ordering = ('user',)


class SurveyAdmin(ModelAdminGroup):
    menu_icon = 'success'
    menu_label = _('Survey Admin')
    items = (EndlineUserAdmin,)
    menu_order = 206


modeladmin_register(SurveyAdmin)


# ==== #
# URLS #
# ==== #


@hooks.register('register_admin_urls')
def register_admin_urls():
    return [
        url(r'^coach-surveys/', include(admin_urls, app_name='survey', namespace='coach-survey-admin')),
    ]
