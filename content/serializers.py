from content.models import Challenge, QuizQuestion, QuestionOption
from content.models import Tip
from content.models import Goal, GoalTransaction
from rest_framework import serializers


class QuestionOptionSerializer(serializers.ModelSerializer):
    class Meta:
        model = QuestionOption
        fields = ('id', 'text', 'correct')


class QuestionSerializer(serializers.ModelSerializer):
    options = QuestionOptionSerializer(many=True, read_only=True)

    class Meta:
        model = QuizQuestion
        fields = ('id', 'text', 'options')


class ChallengeSerializer(serializers.ModelSerializer):
    questions = QuestionSerializer(many=True, read_only=True)

    class Meta:
        model = Challenge
        fields = ('id', 'name', 'type', 'activation_date', 'deactivation_date', 'questions')

    def __init__(self, *args, **kwargs):
        super(ChallengeSerializer, self).__init__(*args, **kwargs)

        # get fields to remove
        exclude_set = set()
        if len(args) > 0 and isinstance(args[0], Challenge):
            self.Meta.fields = list(self.Meta.fields)
            if args[0].type != Challenge.CTP_QUIZ:
                exclude_set.add('questions')

        # remove incorrect fields
        for field_name in exclude_set:
            self.fields.pop(field_name)


class TipSerializer(serializers.ModelSerializer):
    article_url = serializers.ReadOnlyField(source='url', read_only=True)
    cover_image_url = serializers.ReadOnlyField(source='get_cover_image_url', read_only=True)
    tags = serializers.ReadOnlyField(source='get_tag_name_list', read_only=True)

    class Meta:
        model = Tip
        fields = ('id', 'title', 'article_url', 'cover_image_url', 'tags')


class GoalTransactionSerializer(serializers.ModelSerializer):

    class Meta:
        model = GoalTransaction
        exclude = ('goal',)


class GoalSerializer(serializers.ModelSerializer):
    transactions = GoalTransactionSerializer(many=True)

    class Meta:
        model = Goal
        exclude = ('user',)
