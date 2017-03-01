
from django.contrib import admin
from django.utils.translation import ugettext as _
from django import forms
import wagtail.contrib.modeladmin.options as wagadmin

from content.admin_views import GoalAdminIndex, UserAdminIndex
from users.models import Profile
from .models import Challenge, FreeTextQuestion, Participant, PictureQuestion, QuestionOption, QuizQuestion
from .models import Goal, GoalTransaction
from .models import Tip, TipFavourite


class QuestionOptionInline(admin.StackedInline):
    model = QuestionOption
    max_num = 5
    extra = 0
    fk_name = 'question'


class QuestionInline(admin.StackedInline):
    model = QuizQuestion
    max_num = 10
    extra = 0


class ChallengeAdminForm(forms.ModelForm):
    def clean(self):
        cleaned_data = super(ChallengeAdminForm, self).clean()
        if self.instance is not None:
            challenge = self.instance
            if challenge.state == Challenge.CST_PUBLISHED and \
                    Participant.objects.filter(challenge_id=challenge.id).count() > 0:
                raise forms.ValidationError(
                    # Translators: Error message on CMS
                    _('Editing of challenges is disallowed when participants have already answered.'),
                    code='challenge_active_error'
                )
        return cleaned_data


@admin.register(Challenge)
class ChallengeAdmin(admin.ModelAdmin):
    form = ChallengeAdminForm
    fieldsets = [
        (None,
         {'fields': ['name', 'type', 'state', 'end_processed']}),
        ('Dates',
         {'fields': ['activation_date', 'deactivation_date']}),
        ('Images',
         {'fields': ['picture']}),
    ]
    list_display = ('name', 'type', 'state', 'activation_date', 'deactivation_date')
    list_filter = ('name', 'type', 'state')
    inlines = [QuestionInline]


@admin.register(FreeTextQuestion)
class QuestionFreeTextAdmin(admin.ModelAdmin):
    fieldsets = [
        (None,
         {'fields': ['challenge', 'text']})
    ]
    list_display = ('challenge', 'text')
    list_filter = ('challenge', 'text')


class QuestionAdminForm(forms.ModelForm):
    def clean(self):
        cleaned_data = super(QuestionAdminForm, self).clean()
        if self.instance is not None and self.instance.challenge is not None:
            challenge = self.instance.challenge
            if challenge.state == Challenge.CST_PUBLISHED and \
                    Participant.objects.filter(challenge_id=challenge.id).count() > 0:
                raise forms.ValidationError(
                    _('Editing of challenges is disallowed when participants have already answered.'),
                    code='challenge_active_error'
                )
        return cleaned_data


@admin.register(QuizQuestion)
class QuestionAdmin(admin.ModelAdmin):
    form = QuestionAdminForm
    fieldsets = [
        (None,
         {'fields': ['challenge', 'text', 'hint']})
    ]
    list_display = ('challenge', 'text')
    list_filter = ('challenge', 'text')
    inlines = [QuestionOptionInline]


class QuestionOptionAdminForm(forms.ModelForm):
    def clean(self):
        cleaned_data = super(QuestionOptionAdminForm, self).clean()
        if self.instance is not None and self.instance.question is not None and \
                self.instance.question.challenge is not None:
            challenge = self.instance.question.challenge
            if challenge.state == Challenge.CST_PUBLISHED and \
                    Participant.objects.filter(challenge_id=challenge.id).count() > 0:
                print(challenge.id)
                raise forms.ValidationError(
                    _('Editing of challenges is disallowed when participants have already answered.'),
                    code='challenge_active_error'
                )
        return cleaned_data


@admin.register(QuestionOption)
class QuestionOptionAdmin(admin.ModelAdmin):
    form = QuestionOptionAdminForm
    fieldsets = [
        (None,
         {'fields': ['question', 'picture', 'text', 'correct']})
    ]
    list_display = ('question', 'text', 'correct')
    list_filter = ('question', 'text', 'correct')


@admin.register(PictureQuestion)
class QuestionPictureAdmin(admin.ModelAdmin):
    fieldsets = [
        (None,
         {'fields': ['challenge', 'text']})
    ]
    list_display = ('challenge', 'text')
    list_filter = ('challenge', 'text')


class TipAdmin(wagadmin.ModelAdmin):
    model = Tip
    menu_order = 200
    list_display = ('title', 'live', 'owner', 'first_published_at')
    list_filter = ('title', 'live', 'owner', 'first_published_at')


@admin.register(TipFavourite)
class TipFavouriteAdmin(admin.ModelAdmin):
    list_display = ('user', 'tip', 'state')
    list_filter = ('user', 'tip', 'state')


class GoalTransactionInline(admin.StackedInline):
    model = GoalTransaction
    max_num = 15
    extra = 0


@admin.register(Goal)
class GoalAdmin(admin.ModelAdmin):
    readonly_fields = ('value', 'weeks', 'weeks_to_now', 'weeks_left', 'days_left', 'weekly_target',
                       'weekly_average',)
    fieldsets = (
        (None, {
            'fields': ('name', 'state', 'start_date', 'end_date', 'target', 'image', 'user')
        }),
        ('Calculated', {
            'fields': ('value', 'weeks', 'weeks_to_now', 'weeks_left', 'days_left', 'weekly_target',
                       'weekly_average',)
        })
    )
    list_display = ('name', 'user', 'target', 'value')
    list_filter = ('user',)
    inlines = (GoalTransactionInline,)


class FrontendGoalAdmin(wagadmin.ModelAdmin):
    model = Goal

    menu_label = _('User Goal Export')
    menu_order = 100

    add_to_settings_menu = False
    # search_fields('name', 'user__username')
    index_view_class = GoalAdminIndex

    list_display = ('get_username', 'goal_category', 'name',
                    'target', 'value', 'progress',
                    'weekly_average', 'weeks', 'weeks_left',
                    'num_weeks_saved', 'num_weeks_saved_below', 'num_weeks_saved_above',
                    'num_weeks_not_saved', 'num_withdrawals', 'num_weekly_target_edited',
                    'num_weekly_target_increased', 'num_weekly_target_decreased', 'weekly_target_original',
                    'weekly_target', 'num_goal_target_edited', 'num_goal_target_increased',
                    'num_goal_target_decreased', 'goal_weeks_initial', 'goal_weeks_current',
                    'start_date', 'is_goal_reached', 'date_achieved',
                    'is_active', 'date_deleted')
    list_filter = ('user',)

    def get_username(self, obj):
        return obj.user.username
    get_username.short_description = 'Username'

    def goal_category(self, obj):
        return obj.prototype
    goal_category.short_description = 'Goal Category'

    def num_weeks_saved(self, obj):
        # TODO: Return number of weeks that the user has saved
        return 0
    num_weeks_saved.short_description = 'Number of weeks saved'

    def num_weeks_saved_below(self, obj):
        # TODO: Return number of weeks saved below target
        return 0
    num_weeks_saved_below.short_description = 'Number of weeks saved below target'

    def num_weeks_saved_above(self, obj):
        # TODO: Return number of weeks saved above target
        return 0
    num_weeks_saved_above.short_description = 'Number of weeks saved above target'

    def num_weeks_not_saved(self, obj):
        # TODO: Return the number of weeks the user hasn't saved
        return 0
    num_weeks_not_saved.short_description = 'Number of weeks not saved'

    def num_withdrawals(self, obj):
        # TODO: Return the number of times the user has withdrawn
        return 0
    num_withdrawals.short_description = 'Number of withdrawals'

    def num_weekly_target_edited(self, obj):
        # TODO: Return the number of times the user has edited their weekly target
        return 0
    num_weekly_target_edited.short_description = 'Number of weekly target edits'

    def num_weekly_target_increased(self, obj):
        # TODO: Return the number of times weekly target increased
        return 0
    num_weekly_target_increased.short_description = 'Weekly target increased'

    def num_weekly_target_decreased(self, obj):
        # TODO: Return the number of times weekly target decreased
        return 0
    num_weekly_target_decreased.short_description = 'Weekly target decreased'

    def weekly_target_original(self, obj):
        # TODO: Return the original (first) weekly target
        return 0
    weekly_target_original.short_description = 'Original weekly target'

    def num_goal_target_edited(self, obj):
        # TODO: Return the number of times the goals target was edited
        return 0
    num_goal_target_edited.short_description = 'Times goal target edited'

    def num_goal_target_increased(self, obj):
        # TODO: Return the number of times goal target increased
        return 0
    num_goal_target_increased.short_description = 'Goal target increased'

    def num_goal_target_decreased(self, obj):
        # TODO: Return the number of times goal target decreased
        return 0
    num_goal_target_decreased.short_description = 'Goal target decreased'

    def goal_weeks_initial(self, obj):
        # TODO: Return the initial number of goal weeks (When goal was set)
        return 0
    goal_weeks_initial.short_description = 'Initial number of goal weeks'

    def goal_weeks_current(self, obj):
        # TODO: Return the current number of weeks for the goal
        # Current weeks left or total weeks of goal??
        return 0
    goal_weeks_current.short_description = 'Current number of goal weeks'

    def date_achieved(self, obj):
        # TODO: Return the date the goal was achieved
        return 0
    date_achieved.short_description = 'Date goal was achieved'

    def date_deleted(self, obj):
        # TODO: Implement date deleted field on Goal model
        return 0
    date_deleted.short_description = 'Date goal was deleted'


class FrontendUserAdmin(wagadmin.ModelAdmin):
    model = Profile

    menu_label = _('Users Export')
    menu_order = 100

    add_to_settings_menu = False
    # search_fields('name', 'user__username')
    index_view_class = UserAdminIndex

    list_display = ('gender', 'age')
    list_filter = ('user',)