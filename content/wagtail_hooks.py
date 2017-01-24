
from django.conf.urls import url, include
from django.forms import CheckboxSelectMultiple
from django.utils.translation import ugettext_lazy as _

from wagtail.contrib.modeladmin.options import ModelAdmin, ModelAdminGroup, modeladmin_register
from wagtail.contrib.modeladmin.views import IndexView
from wagtail.wagtailcore import hooks

from .models import Challenge, Participant
from .models import FreeTextQuestion, PictureQuestion, QuizQuestion
from .models import GoalPrototype
from .models import Badge
from content import admin_urls


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

# ============ #
# Participants #
# ============ #


class ParticipantAdmin(ModelAdmin):
    # index_template_name = 'modeladmin/participant/index.html'
    index_view_extra_js = ['js/admin_participant_index.js', 'js/js.cookie.js']
    model = Participant
    # Translators: CMS menu name
    menu_label = _('Participants')
    menu_icon = 'user'
    menu_order = 200
    add_to_settings_menu = False
    list_display = ('user', 'challenge', 'date_created', 'date_completed', 'is_completed', 'mark_is_read')
    list_filter = ('date_created', 'challenge', 'is_read', 'is_shortlisted', 'is_winner')
    search_fields = ('user__id', 'challenge__name',)


class CompetitionsAdminGroup(ModelAdminGroup):
    # Translators: CMS menu name
    menu_label = _('Competitions')
    menu_icon = 'folder-open-inverse'
    menu_order = 200
    items = (ChallengeAdmin, ParticipantAdmin, FreeTextQuestionAdmin, PictureQuestionAdmin, QuizQuestionAdmin)


modeladmin_register(CompetitionsAdminGroup)


@hooks.register('register_admin_urls')
def register_admin_urls():
    return [
        url(r'^participants/', include(admin_urls, app_name='content', namespace='participants')),
    ]


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
    list_display = ('name', 'is_active',)
    add_to_settings_menu = False
    lest_display = ('name',)


class Achievements(ModelAdminGroup):
    # Translators: CMS menu name
    menu_label = _('Achievements')
    menu_icon = 'folder-open-inverse'
    menu_order = 201
    items = (BadgeAdmin,)


modeladmin_register(Achievements)
