from django import forms
from django.contrib import admin
import wagtail.contrib.modeladmin.options as wagadmin
from .models import Challenge, QuizQuestion, QuestionOption, Tip


class QuestionOptionInline(admin.StackedInline):
    model = QuestionOption
    max_num = 5
    extra = 0
    fk_name = 'question'


class QuestionInline(admin.StackedInline):
    model = QuizQuestion
    max_num = 10
    extra = 0


@admin.register(Challenge)
class ChallengeAdmin(admin.ModelAdmin):
    fieldsets = [
        (None,
         {'fields': ['name', 'state', 'end_processed']}),
        ('Dates',
         {'fields': ['activation_date', 'deactivation_date']})

    ]
    list_display = ('name', 'state', 'activation_date', 'deactivation_date')
    list_filter = ('name', 'state')
    inlines = [QuestionInline]


@admin.register(QuizQuestion)
class QuestionAdmin(admin.ModelAdmin):
    fieldsets = [
        (None,
         {'fields': ['challenge', 'text']})
    ]
    list_display = ('challenge', 'text')
    list_filter = ('challenge', 'text')
    inlines = [QuestionOptionInline]


@admin.register(QuestionOption)
class QuestionOptionAdmin(admin.ModelAdmin):
    fieldsets = [
        (None,
         {'fields': ['question', 'picture', 'text']})
    ]
    list_display = ('question', 'text')
    list_filter = ('question', 'text')


class TipAdmin(wagadmin.ModelAdmin):
    model = Tip
    menu_order = 200
    list_display = ('title', 'live', 'owner', 'first_published_at')
    list_filter = ('title', 'live', 'owner', 'first_published_at')
