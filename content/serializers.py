from collections import OrderedDict

from django.contrib.auth.models import User
from django.db.models import Q
from django.utils import timezone
from rest_framework import serializers
from rest_framework.reverse import reverse

from .models import Challenge, FreeTextQuestion, QuestionOption, QuizQuestion, PictureQuestion
from .models import Entry, Participant, ParticipantAnswer, ParticipantFreeText, ParticipantPicture
from .models import Feedback
from .models import Goal, GoalPrototype, GoalTransaction
from .models import Badge, UserBadge
from .models import Tip, TipFavourite


# ============ #
# Achievements #
# ============ #


class BadgeSerializer(serializers.ModelSerializer):
    name = serializers.CharField()
    intro = serializers.CharField()
    image_url = serializers.SerializerMethodField()
    social_url = serializers.SerializerMethodField()

    class Meta:
        model = Badge
        fields = ('name', 'intro', 'image_url', 'social_url')

    def get_image_url(self, obj):
        request = self.context['request']
        if obj.image:
            return request.build_absolute_uri(obj.image.file.url)
        else:
            return None

    def get_social_url(self, obj):
        request = self.context['request']
        if obj.slug:
            return request.build_absolute_uri(reverse('social:badges-detail', kwargs={'slug': obj.slug}))
        else:
            return None


class UserBadgeSerializer(serializers.ModelSerializer):
    earned_on = serializers.DateTimeField()

    class Meta:
        model = UserBadge
        fields = ('earned_on',)

    def to_representation(self, instance):
        """Flattens Badge fields and UserBadge linking model, so the earned_on datetime will be inlined."""
        data = super().to_representation(instance)
        badge_serial = BadgeSerializer(instance.badge, context=self.context)
        data.update(badge_serial.data)
        return data


class ParticipantBadgeSerializer(serializers.ModelSerializer):
    """A special serializer that includes Challenge information"""

    earned_on = serializers.DateTimeField()

    class Meta:
        model = UserBadge
        fields = ('earned_on',)

    def to_representation(self, instance):
        """Flattens Badge fields and UserBadge linking model, so the earned_on datetime will be inlined."""
        data = super().to_representation(instance)
        badge_serial = BadgeSerializer(instance.badge, context=self.context)
        data.update(badge_serial.data)

        participant = instance.participant_set.all().first()
        if participant is not None:
            data['challenge_id'] = participant.challenge.id
        else:
            data['challenge_id'] = None

        return data


# ========== #
# Challenges #
# ========== #


def validate_participant(data, errors):
    """
    Takes serializer input data and returns a valid participant if one can be found.
    Requires keys: participant OR user and challenge
    Returns: participant OR None
    """
    print(data)
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
                data['participant'] = participant.id
                return participant
            except Participant.MultipleObjectsReturned:
                errors.update({'participant': 'Multiple participants exist.'})
            except Participant.DoesNotExist:
                try:
                    participant = Participant.objects.create(user_id=user.id, challenge_id=challenge.id)
                    data['participant'] = participant.id
                    return participant
                except:
                    errors.update({'participant': 'Participant could not be created'})

    return None


class KeyValueField(serializers.Field):
    """A field that takes a field's value as the key and returns the associated value for serialization."""

    labels = {}
    inverted_labels = {}

    def __init__(self, labels, *args, **kwargs):
        self.labels = labels
        # Check to make sure the labels dict is reversible, otherwise
        # deserialization may produce unpredictable results
        inverted = {}
        for k, v in labels.items():
            if v in inverted:
                raise ValueError(
                    'The field is not deserializable with the given labels.'
                    ' Please ensure that labels map 1:1 with values'
                )
            inverted[v] = k
        self.inverted_labels = inverted
        super(KeyValueField, self).__init__(*args, **kwargs)

    def to_representation(self, obj):
        if type(obj) is list:
            return [self.labels.get(o, None) for o in obj]
        else:
            return self.labels.get(obj, None)

    def to_internal_value(self, data):
        if type(data) is list:
            return [self.inverted_labels.get(o, None) for o in data]
        else:
            return self.inverted_labels.get(data, None)


class QuestionOptionSerializer(serializers.ModelSerializer):
    class Meta:
        model = QuestionOption
        fields = ('id', 'text', 'correct')


class QuestionSerializer(serializers.ModelSerializer):
    options = QuestionOptionSerializer(many=True, read_only=True)

    class Meta:
        model = QuizQuestion
        fields = ('id', 'text', 'hint', 'options')


class FreeTextSerializer(serializers.ModelSerializer):
    class Meta:
        model = FreeTextQuestion
        fields = ('id', 'text')


class PictureQuestionSerializer(serializers.ModelSerializer):
    class Meta:
        model = PictureQuestion
        fields = ('id', 'text')


class ChallengeSerializer(serializers.ModelSerializer):
    # challenge type enum mapping
    challenge_types = {Challenge.CTP_QUIZ: 'quiz', Challenge.CTP_PICTURE: 'picture', Challenge.CTP_FREEFORM: 'freeform'}

    image_url = serializers.SerializerMethodField(required=False)
    terms_url = serializers.SerializerMethodField(required=False)
    is_active = serializers.BooleanField(read_only=True)
    questions = QuestionSerializer(many=True, read_only=True, required=False)
    freetext_question = FreeTextSerializer(many=True, read_only=True, required=False)
    picture_question = PictureQuestionSerializer(many=True, read_only=True, required=False)
    type = KeyValueField(read_only=True, labels=challenge_types)

    class Meta:
        model = Challenge
        exclude = ('end_processed', 'picture', 'state', 'terms')

    def __init__(self, *args, **kwargs):
        summary = kwargs.pop('summary', False)
        super(ChallengeSerializer, self).__init__(*args, **kwargs)

        # get fields to remove
        if summary:
            self.fields.pop('questions', None)
            self.fields.pop('freetext_question', None)
        elif self.instance and isinstance(self.instance, Challenge):
            if self.instance.type != Challenge.CTP_QUIZ:
                self.fields.pop('questions', None)
            if self.instance.type != Challenge.CTP_FREEFORM:
                self.fields.pop('freetext_question', None)

    def to_representation(self, instance):
        rep_dict = super(ChallengeSerializer, self).to_representation(instance)

        if instance.type != Challenge.CTP_QUIZ:
            rep_dict.pop('questions', None)
        if instance.type != Challenge.CTP_FREEFORM:
            rep_dict.pop('freetext_question', None)
        if instance.type != Challenge.CTP_PICTURE:
            rep_dict.pop('picture_question', None)

        freetext = rep_dict.pop('freetext_question', None)
        if freetext is not None:
            if len(freetext) > 0:
                rep_dict['freetext_question'] = freetext[0]

        picture_question = rep_dict.pop('picture_question', None)
        if picture_question is not None:
            if len(picture_question) > 0:
                rep_dict['picture_question'] = picture_question[0]

        return rep_dict

    def get_image_url(self, obj):
        request = self.context['request']
        if obj.picture:
            return request.build_absolute_uri(obj.picture.url)
        else:
            return None

    def get_terms_url(self, obj):
        request = self.context['request']
        if obj.terms:
            return request.build_absolute_uri(obj.terms.url)
        else:
            return None


class ParticipantRegisterSerializer(serializers.ModelSerializer):
    user = serializers.PrimaryKeyRelatedField(queryset=User.objects.all())
    challenge = serializers.PrimaryKeyRelatedField(queryset=Challenge.objects.all())

    class Meta:
        model = Participant
        fields = ('id', 'user', 'challenge',)
        read_only_fields = ('id', 'user', 'challenge',)

    def validate_challenge(self, value):
        now = timezone.now()
        if value.activation_date > now:
            raise serializers.ValidationError('Challenge not yet active')
        if value.deactivation_date < now:
            raise serializers.ValidationError('Challenge no longer active')

        return value

    def create(self, validated_data):
        user = validated_data.get('user')
        challenge = validated_data.get('challenge')

        try:
            participant = Participant.objects.get(user=user, challenge=challenge)
        except Participant.DoesNotExist:
            participant = Participant.objects.create(user=user, challenge=challenge)

        return participant


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
        errors = {}

        participant = validate_participant(data, errors)

        if participant is None or len(errors) > 0:
            raise serializers.ValidationError(errors)

        if data.get('answers', None) is not None:
            for answer in data.get('answers', None):
                answer['participant'] = participant.id

        return super(EntrySerializer, self).to_internal_value(data)

    def validate(self, data):
        participant = Participant.objects.get(id=data.get('participant').id)
        answers = data.get('answers')
        if answers is None or not isinstance(answers, list):
            raise serializers.ValidationError('Should be a list of answers.')
        question_ids = [answer['question'].id for answer in data['answers']]
        required_questions = QuizQuestion.objects \
            .filter(challenge_id=participant.challenge_id) \
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
    article_url = serializers.SerializerMethodField()
    cover_image_url = serializers.SerializerMethodField()
    is_favourite = serializers.SerializerMethodField()
    tags = serializers.ReadOnlyField(source='get_tag_name_list', read_only=True)

    def get_article_url(self, obj):
        request = self.context['request']
        return request.build_absolute_uri(obj.url)

    def get_cover_image_url(self, obj):
        request = self.context['request']
        if obj.cover_image:
            return request.build_absolute_uri(obj.cover_image.file.url)
        else:
            return None

    def get_is_favourite(self, obj):
        request = self.context['request']
        if obj.favourites.filter(user_id=request.user.id, state=TipFavourite.TFST_ACTIVE).exists():
            return True
        else:
            return False

    @staticmethod
    def setup_prefetch_related(queryset):
        queryset = queryset.prefetch_related('favourites')
        return queryset

    class Meta:
        model = Tip
        fields = ('id', 'title', 'intro', 'article_url', 'cover_image_url', 'is_favourite', 'tags')


class CurrentUserDefault(object):
    def set_context(self, serializer_field):
        self.goal = Goal.objects.get(serializer_field.context['goal'])

    def __call__(self):
        return self.goal


class ParticipantPictureSerializer(serializers.ModelSerializer):
    participant = serializers.PrimaryKeyRelatedField(queryset=Participant.objects.all(), required=False)

    class Meta:
        model = ParticipantPicture
        fields = ('participant', 'question', 'picture', 'date_answered', 'date_saved')
        read_only_fields = ('date_saved',)
        extra_kwargs = {'picture': {'required': False}}

    def to_internal_value(self, data):
        errors = {}

        participant = validate_participant(data, errors)

        if participant is None or len(errors) > 0:
            raise serializers.ValidationError(errors)

        try:
            data['picture'] = self.context.get('request').files['file']
        except:
            pass

        return super(ParticipantPictureSerializer, self).to_internal_value(data=data)


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


# ===== #
# Goals #
# ===== #


class GoalPrototypeSerializer(serializers.ModelSerializer):
    name = serializers.CharField()
    image_url = serializers.SerializerMethodField()
    num_users = serializers.ReadOnlyField()
    default_price = serializers.DecimalField(18, 2, coerce_to_string=False)

    class Meta:
        model = GoalPrototype
        fields = ('id', 'name', 'image_url', "num_users", "default_price")

    def get_image_url(self, obj):
        request = self.context['request']
        if obj.image:
            return request.build_absolute_uri(obj.image.file.url)
        else:
            return None


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

        created_trans = [gt for gt in trans if (gt.date, gt.value, gt.goal.id) not in exist]

        for t in created_trans:
            t.save()

        return created_trans


class GoalTransactionSerializer(serializers.ModelSerializer):
    value = serializers.DecimalField(18, 2, coerce_to_string=False)

    class Meta:
        model = GoalTransaction
        exclude = ('goal', 'id',)
        # TODO: Set up ListSerializer
        list_serializer_class = GoalTransactionListSerializer


class GoalSerializer(serializers.ModelSerializer):
    name = serializers.CharField()
    prototype = serializers.PrimaryKeyRelatedField(queryset=GoalPrototype.objects.all(), allow_null=True,
                                                   required=False)
    start_date = serializers.DateField()
    end_date = serializers.DateField()
    value = serializers.ReadOnlyField()
    target = serializers.DecimalField(18, 2, coerce_to_string=False)
    week_count = serializers.ReadOnlyField()
    week_count_to_now = serializers.ReadOnlyField()
    weekly_average = serializers.ReadOnlyField()
    weekly_target = serializers.ReadOnlyField()
    user = serializers.PrimaryKeyRelatedField(read_only=True, default=serializers.CurrentUserDefault())
    image_url = serializers.SerializerMethodField()
    new_badges = UserBadgeSerializer(many=True, required=False, read_only=True)
    transactions = GoalTransactionSerializer(required=False, many=True)
    transactions_url = serializers.HyperlinkedIdentityField('api:goals-transactions')
    weekly_totals = serializers.SerializerMethodField()

    class Meta:
        model = Goal
        fields = '__all__'
        read_only_fields = ('id', 'weekly_totals')
        extra_kwargs = {'image': {'write_only': True}}

    def get_image_url(self, obj):
        request = self.context['request']
        if obj.image:
            return reverse('api:goal-image', kwargs={'goal_pk': obj.pk}, request=request)
        elif obj.prototype and obj.prototype.image:
            return request.build_absolute_uri(obj.prototype.image.file.url)
        else:
            return None

    def get_weekly_totals(self, obj):
        d = OrderedDict()
        for week in obj.get_weekly_aggregates():
            d[str(week.id)] = float(week.value)
        return d

    def get_new_badges(self, obj):
        # Relation handled in method field because it is another level deep
        user_badges = UserBadge.objects.filter(user=obj.user)
        return UserBadgeSerializer(user_badges, many=True, context=self.context).data

    def validate(self, attrs):
        data = super().validate(attrs)

        if attrs['end_date'] < attrs['start_date']:
            raise serializers.ValidationError('End date is earlier than start date.')

        return data

    def create(self, validated_data):
        transactions = validated_data.pop('transactions', [])
        goal = Goal.objects.create(**validated_data)

        for trans_data in transactions:
            GoalTransaction.objects.create(goal=goal, **trans_data)

        return goal

    def update(self, instance, validated_data):
        # Transactions are ignored on update
        transactions_data = validated_data.pop('transactions', [])

        # Update Goal
        instance.name = validated_data.get('name', instance.name)
        instance.start_date = validated_data.get('start_date', instance.start_date)
        instance.end_date = validated_data.get('end_date', instance.end_date)
        instance.target = validated_data.get('target', instance.target)
        # TODO: Image Field
        # Goal owner can not be updated.
        # instance.user = validated_data.get('user', instance.user)

        for t in transactions_data:
            t['goal'] = instance

        instance.save()

        for t in GoalTransactionSerializer(many=True, context=self.context).create(transactions_data):
            # Add to instance in memory for return purposes.
            instance.transactions.add(t)

        return instance


class AchievementStatSerializer(serializers.Serializer):
    weekly_streak = serializers.ReadOnlyField()
    badges = UserBadgeSerializer(many=True, read_only=True)
    last_saving_datetime = serializers.ReadOnlyField()
    weeks_since_saved = serializers.ReadOnlyField()

    class Meta:
        fields = '__all__'


############
# Feedback #
############


class FeedbackSerializer(serializers.ModelSerializer):
    # feedback types enum mapping
    feedback_types = {
        Feedback.FT_ASK: 'ask',
        Feedback.FT_GENERAL: 'general',
        Feedback.FT_PARTNER: 'partner',
        Feedback.FT_REPORT: 'report',
    }

    user = serializers.PrimaryKeyRelatedField(queryset=User.objects.all(), required=False)
    type = KeyValueField(labels=feedback_types)

    class Meta:
        model = Feedback
        fields = ('date_created', 'text', 'type', 'user',)

    def create(self, validated_data):
        return Feedback.objects.create(**validated_data)
