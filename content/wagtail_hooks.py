
from django.utils.translation import ugettext_lazy as _
from wagtail.contrib.modeladmin.options import ModelAdmin, ModelAdminGroup, modeladmin_register

from .models import Challenge
from .models import QuizQuestion
from .models import GoalPrototype


# ========== #
# Challenges #
# ========== #


class ChallengeAdmin(ModelAdmin):
    model = Challenge
    add_to_settings_menu = False
    list_display = ('name', 'type', 'state', 'activation_date', 'deactivation_date', 'is_active_html')
    list_filter = ('name', 'type', 'state')
    search_fields = ('name',)


class QuizQuestionAdmin(ModelAdmin):
    model = QuizQuestion
    menu_label = _('Quiz Questions')
    add_to_settings_menu = False
    list_display = ('challenge', 'text_truncated', 'option_count',)
    list_filter = ('challenge',)
    search_fields = ('challenge',)


class CompetitionsAdminGroup(ModelAdminGroup):
    menu_label = _('Competitions')
    menu_icon = 'folder-open-inverse'
    menu_order = 200
    items = (ChallengeAdmin, QuizQuestionAdmin)


modeladmin_register(CompetitionsAdminGroup)


# ===== #
# Goals #
# ===== #


class GoalPrototypeAdmin(ModelAdmin):
    model = GoalPrototype
    menu_label = _('Goal Prototypes')
    menu_order = 200
    add_to_settings_menu = False
    list_display = ('name',)
    list_filter = ('state',)
    search_fields = ('name',)


modeladmin_register(GoalPrototypeAdmin)
