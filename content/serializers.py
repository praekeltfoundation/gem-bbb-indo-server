from content.models import Challenge, Question, QuestionOption
from content.models import Tip
from rest_framework import serializers


class QuestionOptionSerializer(serializers.ModelSerializer):

    class Meta:
        model = QuestionOption
        fields = ('id', 'text')


class QuestionSerializer(serializers.ModelSerializer):
    options = QuestionOptionSerializer(many=True, read_only=True)

    class Meta:
        model = Question
        fields = ('id', 'text', 'options')


class ChallengeSerializer(serializers.ModelSerializer):
    questions = QuestionSerializer(many=True, read_only=True)

    class Meta:
        model = Challenge
        fields = ('id', 'name', 'questions')


class TipSerializer(serializers.ModelSerializer):
    article_url = serializers.ReadOnlyField(source='url', read_only=True)
    cover_image_url = serializers.ReadOnlyField(source='get_cover_image_url', read_only=True)
    tags = serializers.ReadOnlyField(source='get_tag_name_list', read_only=True)

    class Meta:
        model = Tip
        fields = ('id', 'title', 'article_url', 'cover_image_url', 'tags')
