from django import forms
from django.contrib import admin
import wagtail.contrib.modeladmin.options as wagadmin
from .models import Challenge, Goal, GoalTransaction, Participant, QuestionOption, QuizQuestion, Tip


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
                    'Editing of challenges is disallowed when participants have already answered.',
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
         {'fields': ['activation_date', 'deactivation_date']})

    ]
    list_display = ('name', 'type', 'state', 'activation_date', 'deactivation_date')
    list_filter = ('name', 'type', 'state')
    inlines = [QuestionInline]


class QuestionAdminForm(forms.ModelForm):
    def clean(self):
        cleaned_data = super(QuestionAdminForm, self).clean()
        if self.instance is not None and self.instance.challenge is not None:
            challenge = self.instance.challenge
            if challenge.state == Challenge.CST_PUBLISHED and \
                    Participant.objects.filter(challenge_id=challenge.id).count() > 0:
                raise forms.ValidationError(
                    'Editing of challenges is disallowed when participants have already answered.',
                    code='challenge_active_error'
                )
        return cleaned_data


@admin.register(QuizQuestion)
class QuestionAdmin(admin.ModelAdmin):
    form = QuestionAdminForm
    fieldsets = [
        (None,
         {'fields': ['challenge', 'text']})
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
                    'Editing of challenges is disallowed when participants have already answered.',
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


class TipAdmin(wagadmin.ModelAdmin):
    model = Tip
    menu_order = 200
    list_display = ('title', 'live', 'owner', 'first_published_at')
    list_filter = ('title', 'live', 'owner', 'first_published_at')


class GoalTransactionInline(admin.StackedInline):
    model = GoalTransaction
    max_num = 15
    extra = 0


@admin.register(Goal)
class GoalAdmin(admin.ModelAdmin):
    list_display = ('name', 'user', 'value')
    list_filter = ('user',)
    inlines = (GoalTransactionInline,)
