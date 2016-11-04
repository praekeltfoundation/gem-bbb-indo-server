
from django.contrib.auth.models import User
from django.shortcuts import reverse
from rest_framework import serializers

from content.models import Tip
from content.models import Goal, GoalTransaction
from content.models import Challenge, Entry, FreeTextQuestion, Participant, ParticipantAnswer, ParticipantFreeText, \
    QuestionOption, QuizQuestion


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


class ParticipantAnswerSerializer(serializers.ModelSerializer):
    question = serializers.PrimaryKeyRelatedField(queryset=QuizQuestion.objects.all())
    selected_option = serializers.PrimaryKeyRelatedField(queryset=QuestionOption.objects.all())

    class Meta:
        model = ParticipantAnswer
        fields = ('id', 'question', 'selected_option', 'date_answered', 'date_saved')
        read_only_fields = ('id', 'date_saved')


class EntrySerializer(serializers.ModelSerializer):
    participant = serializers.PrimaryKeyRelatedField(queryset=Participant.objects.all())
    answers = ParticipantAnswerSerializer(many=True)

    class Meta:
        model = Entry
        fields = ('id', 'participant', 'date_saved', 'date_completed', 'answers')
        read_only_fields = ('id', 'date_saved')

    def to_internal_value(self, data):
        user = data.pop('user', None)
        challenge = data.pop('challenge', None)

        if data.get('participant') is None:
            if user is None or challenge is None:
                raise serializers.ValidationError(
                    {'participant': 'Must specify either participant or user and challenge.'})

            try:
                User.objects.get(id=user)
            except User.DoesNotExist:
                raise serializers.ValidationError({'user': 'No such user.'})

            try:
                Challenge.objects.get(id=challenge)
            except Challenge.DoesNotExist:
                raise serializers.ValidationError({'challenge': 'No such challenge.'})

            try:
                participant = Participant.objects.get(user_id=user, challenge_id=challenge)
                data['participant'] = participant.id
            except:
                try:
                    participant = Participant.objects.create(challenge_id=challenge, user_id=user)
                    data['participant'] = participant.id
                except Participant.DoesNotExist:
                    raise serializers.ValidationError({'user': 'Could not create participant.'})

        return super(EntrySerializer, self).to_internal_value(data)

    def validate(self, data):
        participant = Participant.objects.get(id=data.get('participant').id)
        answers = data.get('answers')
        if answers is None or not isinstance(answers, list):
            raise serializers.ValidationError('Should be a list of answers.')
        question_ids = [answer['question'].id for answer in data['answers']]
        required_questions = QuizQuestion.objects\
            .filter(challenge_id=participant.challenge_id)\
            .values_list('id', flat=True)
        if not set(required_questions).issubset(question_ids):
            raise serializers.ValidationError('Not all questions answered.')
        return data

    def create(self, validated_data):
        entry = Entry.objects.create(participant=validated_data.get('participant'),
                                     date_completed=validated_data.get('date_completed'))
        answers = validated_data.get('answers')
        for answer in answers:
            answer['entry'] = entry
            ParticipantAnswer.objects.create(**answer)

        return entry


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
        exclude = ('goal', 'id',)


class GoalSerializer(serializers.ModelSerializer):
    transactions = GoalTransactionSerializer(required=False, many=True)
    user = serializers.PrimaryKeyRelatedField(queryset=User.objects.all())
    image_url = serializers.SerializerMethodField()

    class Meta:
        model = Goal
        fields = '__all__'
        read_only_fields = ('id',)
        extra_kwargs = {'image': {'write_only': True}}

    def get_image_url(self, obj):
        return reverse('goal-image', kwargs={'goal_pk': obj.pk})

    def create(self, validated_data):
        transactions = validated_data.pop('transactions', [])
        goal = Goal.objects.create(**validated_data)

        for trans_data in transactions:
            GoalTransaction.objects.create(goal=goal, **trans_data)

        return goal

    def update(self, instance, validated_data):
        transactions_data = validated_data.pop('transactions', [])
        transactions = instance.transactions.all()
        trans_lookup = {datum.get('id', None) for datum in transactions_data}

        # Update Goal
        instance.name = validated_data.get('name', instance.name)
        instance.start_date = validated_data.get('start_date', instance.start_date)
        instance.end_date = validated_data.get('validate_date', instance.end_date)
        instance.value = validated_data.get('value', instance.value)
        # TODO: Image Field
        instance.user = validated_data.get('user', instance.user)

        instance.save()

        # Update Transactions
        # TODO: Transactions

        return instance


class ParticipantFreeTextSerializer(serializers.ModelSerializer):
    participant = serializers.PrimaryKeyRelatedField(queryset=Participant.objects.all(), required=False)
    question = serializers.PrimaryKeyRelatedField(queryset=FreeTextQuestion.objects.all(), required=False)

    class Meta:
        model = ParticipantFreeText
        fields = ('id', 'participant', 'question', 'answered_date', 'saved_date', 'text')
        read_only_fields = ('id', 'saved_date')

    def to_internal_value(self, data):
        user = data.pop('user')
        challenge = data.pop('challenge')
        errors = {}

        if data.get('participant') is None and data.get('question') is None:
            try:
                challenge = Challenge.objects.get(challenge)
            except Challenge.DoesNotExist:
                errors.update({'challenge': 'Challenge does not exist'})

            try:
                user = User.objects.get(user)
            except User.DoesNotExist:
                errors.update({'user': 'User does not exist'})

            if len(errors) <= 0:
                try:
                    data['participant'] = Participant.objects.get(challenge_id=challenge, user_id=user)
                except Participant.DoesNotExist:
                    try:
                        data['participant'] = Participant.objects.create(user=user, challenge=challenge)
                        data['question'] = challenge.freetext_question
                    except:
                        errors.update({'participant': 'Participant could not be created'})

        if len(errors) > 0:
            raise serializers.ValidationError(errors)

        return super(ParticipantFreeTextSerializer, self).to_internal_value(data=data)

    def create(self, validated_data):
        return ParticipantFreeText(**validated_data)

    def update(self, instance, validated_data):
        pass
