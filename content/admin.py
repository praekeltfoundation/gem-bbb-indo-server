
from django.contrib import admin
from django.utils.translation import ugettext as _
from django import forms
import wagtail.contrib.modeladmin.options as wagadmin

from content.admin_views import ReportAdminIndex
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


class FrontendReportAdmin(wagadmin.ModelAdmin):
    menu_label = _('Reports')
    add_to_settings_menu = False
    index_view_class = ReportAdminIndex

# class FrontendGoalAdmin(wagadmin.ModelAdmin):
#     model = Goal
#
#     menu_label = _('User Goal Export')
#     menu_order = 100
#
#     add_to_settings_menu = False
#     # search_fields('name', 'user__username')
#     index_view_class = ReportAdminIndex
#
#     list_display = ('name',)
#     list_filter = ('user',)

#
# class FrontendUserAdmin(wagadmin.ModelAdmin):
#     model = Profile
#
#     menu_label = _('Users Export')
#     menu_order = 200
#
#     add_to_settings_menu = False
#     # search_fields('name', 'user__username')
#     index_view_class = UserAdminIndex
#
#     list_display = ('gender', 'age')
#     list_filter = ('user',)
#
#
# class FrontendSavingsAdmin(wagadmin.ModelAdmin):
#     model = Goal
#
#     menu_label = _('Savings Export')
#     menu_order = 300
#
#     add_to_settings_menu = False
#     index_view_class = SavingsAdminIndex
#
#     list_display = ('name', 'target')