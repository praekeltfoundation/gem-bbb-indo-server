from django.shortcuts import render
from rest_framework import viewsets
from .models import Question,Challenge
from.serializers import QuestionSerializer
# Create your views here.

class QuestionsPerChallenge(viewsets.ModelViewSet):
    serializer_class = QuestionSerializer
    # Question.objects.filter(challenge__name=param)
