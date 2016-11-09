from django.contrib.auth.models import User
from django.utils import timezone
from django.db.models import Q
from rest_framework import serializers
from rest_framework.reverse import reverse

from content.models import Challenge, Entry, FreeTextQuestion, Participant, ParticipantAnswer, ParticipantFreeText, \
    QuestionOption, QuizQuestion
from content.models import Goal, GoalTransaction
from content.models import Tip


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


class CurrentUserDefault(object):
    def set_context(self, serializer_field):
        self.goal = Goal.objects.get(serializer_field.context['goal'])

    def __call__(self):
        return self.goal


class GoalTransactionListSerializer(serializers.ListSerializer):
    def create(self, validated_data):
        # TODO: Find alternative to lookup in Python. Possibly direct SQL.
        # TODO: Get all transactions for Goal instead of using Q object.
        q = Q()
        trans = []
        for t in validated_data:
            # eg:(date=... AND value=...) OR (date=... AND value=...)
            q |= Q(goal_id=t['goal'].id) & Q(date=t['date']) & Q(value=t['value'])
            trans.append(GoalTransaction(**t))
        exist = {(g.date, g.value, g.goal.id) for g in GoalTransaction.objects.filter(q)}
        return GoalTransaction.objects.bulk_create([gt for gt in trans if (gt.date, gt.value, gt.goal.id) not in exist])


class GoalTransactionSerializer(serializers.ModelSerializer):

    class Meta:
        model = GoalTransaction
        exclude = ('goal', 'id',)
        # TODO: Set up ListSerializer
        list_serializer_class = GoalTransactionListSerializer


class GoalSerializer(serializers.ModelSerializer):
    transactions = GoalTransactionSerializer(required=False, many=True)
    transactions_url = serializers.HyperlinkedIdentityField('api:goals-transactions')
    user = serializers.PrimaryKeyRelatedField(read_only=True, default=serializers.CurrentUserDefault())
    image_url = serializers.SerializerMethodField()

    class Meta:
        model = Goal
        fields = '__all__'
        read_only_fields = ('id',)
        extra_kwargs = {'image': {'write_only': True}}

    def get_image_url(self, obj):
        return reverse('goal-image', kwargs={'goal_pk': obj.pk}, request=self.context['request'])

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


def validate_participant(data, errors):
    user = data.pop('user', None)
    challenge = data.pop('challenge', None)

    if data.get('participant', None) is not None:
        try:
            participant = Participant.objects.get(id=data.get('participant'))
            return participant
        except Participant.MultipleObjectsReturned:
            errors.update({'participant': 'Multiple participants exist.'})
        except Participant.DoesNotExist:
            errors.update({'participant': 'No such participant exists.'})
    else:
        if challenge is None:
            errors.update({'challenge': 'Must specify either participant or challenge.'})
        else:
            try:
                challenge = Challenge.objects.get(id=challenge)
            except Challenge.DoesNotExist:
                errors.update({'challenge': 'Challenge does not exist'})

        if user is None:
            errors.update({'user': 'Must specify either participant or user'})
        else:
            try:
                user = User.objects.get(id=user)
            except User.DoesNotExist:
                errors.update({'user': 'User does not exist'})

        if len(errors) <= 0:
            try:
                participant = Participant.objects.get(challenge_id=challenge.id, user_id=user.id)
                return participant
            except Participant.MultipleObjectsReturned:
                errors.update({'participant': 'Multiple participants exist.'})
            except Participant.DoesNotExist:
                try:
                    participant = Participant.objects.create(user_id=user.id, challenge_id=challenge.id)
                    return participant
                except:
                    errors.update({'participant': 'Participant could not be created'})

    return None


class ParticipantFreeTextSerializer(serializers.ModelSerializer):
    participant = serializers.PrimaryKeyRelatedField(queryset=Participant.objects.all(), required=False)
    question = serializers.PrimaryKeyRelatedField(queryset=FreeTextQuestion.objects.all(), required=False)

    class Meta:
        model = ParticipantFreeText
        fields = ('id', 'participant', 'question', 'date_answered', 'date_saved', 'text')
        read_only_fields = ('id', 'saved_date')

    def to_internal_value(self, data):
        errors = {}

        participant = validate_participant(data, errors)

        if participant is None:
            raise serializers.ValidationError(errors)
        else:
            data['participant'] = participant.id

        question_id = data.get('question', None)
        if question_id is not None:
            try:
                FreeTextQuestion.objects.get(id=data.get('question', None))
            except FreeTextQuestion.MultipleObjectsReturned:
                errors.update({'question': 'Multiple questions exist.'})
            except FreeTextQuestion.DoesNotExist:
                errors.update({'question': 'No such question exists.'})
            except:
                errors.update({'question': 'Unknown error with question.'})
        else:
            try:
                question = participant.challenge.freetext_question
                data['question'] = question.id
            except:
                errors.update({'question': 'Question does not exist.'})

        if len(errors) > 0:
            raise serializers.ValidationError(errors)

        return super(ParticipantFreeTextSerializer, self).to_internal_value(data=data)

    def save(self, **kwargs):
        try:
            answer = ParticipantFreeText.objects.get(participant_id=self.validated_data.get('participant'),
                                                     question_id=self.validated_data.get('question'))
            answer.text = self.validated_data.get('text')
        except ParticipantFreeText.DoesNotExist:
            answer = ParticipantFreeText(**self.validated_data)
        except ParticipantFreeText.MultipleObjectsReturned:
            raise serializers.DjangoValidationError('Multiple answers for this participant.', code='multi_answer')
        return answer.save()

    def create(self, validated_data):
        return ParticipantFreeText.objects.create(**validated_data)

    def update(self, instance, validated_data):
        instance.date_saved = timezone.now()
        if validated_data.get('text') is not None:
            instance.text = validated_data.get('text')
        instance.save()
        return instance
