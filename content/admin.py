from django.contrib import admin
from .models import Challenge, Question, QuestionOption


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


@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    fieldsets = [
        (None,
         {'fields': ['challenge', 'picture', 'text', 'type']})
    ]
    list_display = ('challenge', 'text', 'type')
    list_filter = ('challenge', 'text', 'type')


@admin.register(QuestionOption)
class QuestionOptionAdmin(admin.ModelAdmin):
    fieldsets = [
        (None,
         {'fields': ['question', 'picture', 'text']})
    ]
    list_display = ('question', 'text')
    list_filter = ('question', 'text')
