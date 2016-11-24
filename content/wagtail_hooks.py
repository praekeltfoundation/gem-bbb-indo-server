
from wagtail.contrib.modeladmin.options import ModelAdmin, ModelAdminGroup, modeladmin_register

from .models import Challenge
from .models import QuizQuestion


class ChallengeAdmin(ModelAdmin):
    model = Challenge
    add_to_settings_menu = False
    list_display = ('name', 'type', 'state', 'activation_date', 'deactivation_date', 'is_active_html')
    list_filter = ('name', 'type', 'state')
    search_fields = ('name',)


class QuizQuestionAdmin(ModelAdmin):
    model = QuizQuestion
    add_to_settings_menu = False
    list_display = ('challenge', 'text', 'hint',)
    list_filter = ('challenge',)
    search_fields = ('challenge',)


class CompetitionsAdminGroup(ModelAdminGroup):
    menu_label = 'Competitions'
    menu_icon = 'folder-open-inverse'
    menu_order = 200
    items = (ChallengeAdmin, QuizQuestionAdmin)


modeladmin_register(CompetitionsAdminGroup)
