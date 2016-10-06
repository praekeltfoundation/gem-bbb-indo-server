from content.models import Challenge, Question, QuestionOption
from rest_framework import serializers


class ChallengeSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Challenge
        fields = ('name')

class QuestionSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Challenge
        fields = ('name','text','type')

class QuestionOptionSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = QuestionOption
        fields = ('name','text','next')