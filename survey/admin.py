from django.contrib import admin


from .models import EndlineSurveySelectUser


def make_receive_survey(modeladmin, request, queryset):
    queryset.update(receive_survey=True)
make_receive_survey.short_description = "Mark the users as eligible for the survey"


def make_not_receive_survey(modeladmin, request, queryset):
    queryset.update(receive_survey=False)
make_not_receive_survey.short_description = "Mark the users as not eligible for the survey"


@admin.register(EndlineSurveySelectUser)
class EndlineSurveyAdmin(admin.ModelAdmin):
    model = EndlineSurveySelectUser
    menu_order = 210
    list_display = ('user', 'receive_survey', 'survey_completed',)
    list_editable = ('receive_survey',)
    actions = [make_receive_survey, make_not_receive_survey]
