
from django.utils.translation import ugettext_lazy as _
from wagtail.contrib.modeladmin.options import ModelAdmin, ModelAdminGroup, modeladmin_register

from .models import Challenge
from .models import FreeTextQuestion, PictureQuestion, QuizQuestion
from .models import GoalPrototype
from .models import Badge


# ========== #
# Challenges #
# ========== #


class ChallengeAdmin(ModelAdmin):
    model = Challenge
    add_to_settings_menu = False
    list_display = ('name', 'type', 'state', 'activation_date', 'deactivation_date', 'is_active_html')
    list_filter = ('name', 'type', 'state')
    search_fields = ('name',)


class FreeTextQuestionAdmin(ModelAdmin):
    model = FreeTextQuestion
    add_to_settings_menu = False
    list_display = ('challenge', 'text_truncated',)
    list_filter = ('challenge',)
    search_fields = ('challenge',)


class PictureQuestionAdmin(ModelAdmin):
    model = PictureQuestion
    menu_label = _('Picture Questions')
    add_to_settings_menu = False
    list_display = ('challenge', 'text_truncated',)
    list_filter = ('challenge',)
    search_fields = ('challenge',)


class QuizQuestionAdmin(ModelAdmin):
    model = QuizQuestion
    menu_label = _('Quiz Questions')
    add_to_settings_menu = False
    list_display = ('challenge', 'text_truncated', 'option_count',)
    list_filter = ('challenge',)
    search_fields = ('challenge',)


class CompetitionsAdminGroup(ModelAdminGroup):
    # Translators: CMS menu name
    menu_label = _('Competitions')
    menu_icon = 'folder-open-inverse'
    menu_order = 200
    items = (ChallengeAdmin, FreeTextQuestionAdmin, PictureQuestionAdmin, QuizQuestionAdmin)


modeladmin_register(CompetitionsAdminGroup)


# ===== #
# Goals #
# ===== #


class GoalPrototypeAdmin(ModelAdmin):
    model = GoalPrototype
    # Translators: CMS menu name
    menu_label = _('Goal Prototypes')
    menu_order = 200
    add_to_settings_menu = False
    list_display = ('name', 'state',)
    list_filter = ('state',)
    search_fields = ('name',)


modeladmin_register(GoalPrototypeAdmin)


# ============ #
# Achievements #
# ============ #


class BadgeAdmin(ModelAdmin):
    model = Badge
    # Translators: CMS menu name
    menu_label = _('Badges')
    menu_order = 100
    add_to_settings_menu = False
    lest_display = ('name',)


class Achievements(ModelAdminGroup):
    # Translators: CMS menu name
    menu_label = _('Achievements')
    menu_icon = 'folder-open-inverse'
    menu_order = 201
    items = (BadgeAdmin,)


modeladmin_register(Achievements)
