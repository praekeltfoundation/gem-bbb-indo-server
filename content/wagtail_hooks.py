from django.conf.urls import url, include
from django.contrib.auth.models import Permission
from django.core.urlresolvers import reverse
from django.utils.translation import ugettext_lazy as _

from wagtail.contrib.modeladmin.options import ModelAdmin, ModelAdminGroup, modeladmin_register
from wagtail.wagtailadmin.menu import MenuItem
from wagtail.wagtailcore import hooks

from content.menu import ReportMenuItem
from .models import Feedback
from .models import Challenge, Participant, CustomNotification, ParticipantFreeText, ParticipantPicture
from .models import FreeTextQuestion, PictureQuestion, QuizQuestion
from .models import GoalPrototype
from .models import Badge
from .models import ExpenseCategory, Budget, Expense
from content import admin_urls


# ========== #
# Challenges #
# ========== #


class ChallengeAdmin(ModelAdmin):
    model = Challenge
    add_to_settings_menu = False
    list_display = ('name', 'type', 'state', 'activation_date', 'deactivation_date',
                    'is_active_html', 'view_participants')
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
    index_view_extra_js = ['js/js.cookie.js', 'js/admin_participant_index.js']
    model = Participant
    # Translators: CMS menu name
    menu_label = _('Participants')
    menu_icon = 'user'
    menu_order = 200
    add_to_settings_menu = False
    list_display = ('user', 'challenge', 'date_created', 'date_completed',
                    'mark_is_read', 'mark_is_shortlisted', 'mark_is_winner')
    list_filter = ('date_created', 'challenge', 'is_read', 'is_shortlisted', 'is_winner')
    search_fields = ('user__id', 'challenge__name',)


# =================== #
# FreeTextParticipant #
# =================== #

class FreeTextParticipantAdmin(ModelAdmin):
    # index_template_name = 'modeladmin/participant/index.html'
    index_view_extra_js = ['js/js.cookie.js', 'js/admin_participant_index.js']
    model = ParticipantFreeText
    # Translators: CMS menu name
    menu_label = _('Free Text Submissions')
    menu_icon = 'user'
    menu_order = 200
    add_to_settings_menu = False
    list_display = ('participant_user','challenge', 'challenge_created_on', 'question', 'text', 'date_answered',
                    'read', 'shortlisted', 'winner')
    list_filter = ('participant__date_created', 'participant__challenge',
                   'participant__is_read', 'participant__is_shortlisted', 'participant__is_winner')
    search_fields = ('participant__user__id', 'participant__challenge__name',)


# ================== #
# PictureParticipant #
# ================== #

class PictureParticipantAdmin(ModelAdmin):
    # index_template_name = 'modeladmin/participant/index.html'
    index_view_extra_js = ['js/js.cookie.js', 'js/admin_participant_index.js', 'js/featherlight.min.js']
    index_view_extra_css = ['css/featherlight.min.css']
    model = ParticipantPicture
    # Translators: CMS menu name
    menu_label = _('Picture Submissions')
    menu_icon = 'user'
    menu_order = 200
    add_to_settings_menu = False
    list_display = ('participant_user', 'challenge', 'challenge_created_on', 'display_picture', 'caption',
                    'date_answered', 'read', 'shortlisted', 'winner')
    list_filter = ('participant__date_created', 'participant__challenge',
                   'participant__is_read', 'participant__is_shortlisted', 'participant__is_winner')
    search_fields = ('participant__user__id', 'participant__challenge__name',)


class CompetitionsAdminGroup(ModelAdminGroup):
    # Translators: CMS menu name
    menu_label = _('Competitions')
    menu_icon = 'folder-open-inverse'
    menu_order = 200
    items = (ChallengeAdmin, ParticipantAdmin,
             FreeTextParticipantAdmin, PictureParticipantAdmin,
             FreeTextQuestionAdmin, PictureQuestionAdmin, QuizQuestionAdmin)


modeladmin_register(CompetitionsAdminGroup)


@hooks.register('register_admin_urls')
def register_admin_urls():
    return [
        url(r'^content/', include(admin_urls, app_name='content', namespace='content-admin')),
    ]


@hooks.register('register_admin_menu_item')
def register_reports_menu_item():
    return ReportMenuItem('Reports', reverse('content-admin:reports-index'), classnames='icon icon-user', order=10000)


@hooks.register('register_permissions')
def view_restricted_page():
    return Permission.objects.filter(codename="access_reports")


@hooks.register('construct_main_menu')
def register_quiz_entry_menu_item(request, menu_items):
    custom_menu_item = MenuItem('Quiz Submissions', reverse('content-admin:challenge-quizentries'), classnames='icon icon-user', order=10001)
    for menu_item in menu_items:
        if menu_item.name == 'competitions':
            for reg_menu_item in menu_item.menu.registered_menu_items:
                if reg_menu_item.name == 'quiz-submissions':
                    return

            menu_item.menu.registered_menu_items.append(custom_menu_item)

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


#######################
# Custom Notification #
#######################


class CustomNotificationAdmin(ModelAdmin):
    model = CustomNotification
    menu_label = _("Custom Notification")
    menu_icon = 'mail'
    list_display = ('message', 'publish_date', 'expiration_date')
    add_to_settings_menu = False


modeladmin_register(CustomNotificationAdmin)


##########
# Budget #
##########


class ExpenseCategoryAdmin(ModelAdmin):
    model = ExpenseCategory
    menu_label = _('Expense Category')
    menu_order = 100
    add_to_settings_menu = False
    list_display = ('name', 'state', 'order')
    list_filter = ('state',)
    search_fields = ('name',)
    ordering = ('order', 'id',)


class BudgetAdmin(ModelAdmin):
    model = Budget
    menu_icon = 'user'
    menu_label = _('User Budget')
    menu_order = 200
    add_to_settings_menu = False
    list_display = ('user_username', 'income', 'savings')
    # list_filter = ('state',)
    search_fields = ('user_username',)

    def user_username(self, obj):
        return obj.user.username


class BudgetGroup(ModelAdminGroup):
    # Translators: CMS menu name
    menu_label = _('Budget')
    menu_icon = 'folder-open-inverse'
    menu_order = 205
    items = (ExpenseCategoryAdmin, BudgetAdmin,)


modeladmin_register(BudgetGroup)


############
# Feedback #
############

class FeedbackAdmin(ModelAdmin):
    model = Feedback
    index_view_extra_js = ['js/js.cookie.js', 'js/admin_participant_index.js']
    menu_icon = 'form'
    list_display = ('date_created', 'user_username', 'type', 'text', 'mark_is_read')
    search_fields = ('text',)
    list_filter = ('type', 'is_read')
    ordering = ('date_created',)

modeladmin_register(FeedbackAdmin)
