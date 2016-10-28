from django import forms

from .models import Challenge, QuizQuestion, QuestionOption


class ChallengeForm(forms.ModelForm):
    class Meta:
        model = Challenge
        fields = ('name', 'activation_date', 'deactivation_date', 'state', 'end_processed')


class QuestionForm(forms.ModelForm):
    class Meta:
        model = QuizQuestion
        fields = ('challenge', 'picture', 'text', 'type')


class QuestionOptionForm(forms.ModelForm):
    class Meta:
        model = QuestionOption
        fields = ('question', 'picture', 'text', 'correct')
