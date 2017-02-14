from collections import OrderedDict

from django.contrib.auth.models import User
from django.shortcuts import get_object_or_404, render
from rest_framework import status
from rest_framework import viewsets
from rest_framework.decorators import list_route, detail_route
from rest_framework.exceptions import NotFound, PermissionDenied, MethodNotAllowed
from rest_framework.generics import GenericAPIView
from rest_framework.parsers import FileUploadParser
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from sendfile import sendfile
from wagtail.wagtailcore.models import Site

from .exceptions import ImageNotFound

from .models import award_entry_badge
from .models import AchievementStat
from .models import Badge, Challenge, Entry
from .models import BadgeSettings, award_challenge_win
from .models import Feedback
from .models import Goal, GoalPrototype
from .models import Participant, ParticipantAnswer, ParticipantFreeText, ParticipantPicture
from .models import Tip, TipFavourite
from .models import WEEK_STREAK_2, WEEK_STREAK_4, WEEK_STREAK_6
from .models import award_first_goal, award_goal_done, award_goal_halfway, award_goal_week_left, \
    award_transaction_first, award_week_streak
from .models import award_weekly_target_badge, WEEKLY_TARGET_2, WEEKLY_TARGET_4, WEEKLY_TARGET_6
from .permissions import IsAdminOrOwner, IsUserSelf
from .serializers import AchievementStatSerializer, UserBadgeSerializer
from .serializers import ChallengeSerializer, EntrySerializer
from .serializers import FeedbackSerializer
from .serializers import GoalPrototypeSerializer, GoalSerializer, GoalTransactionSerializer
from .serializers import ParticipantAnswerSerializer, ParticipantFreeTextSerializer, ParticipantPictureSerializer, \
    ParticipantRegisterSerializer
from .serializers import TipSerializer
import json


# ========== #
# Challenges #
# ========== #


class ChallengeImageView(GenericAPIView):
    queryset = Challenge.objects.all()
    permission_classes = (IsAuthenticated,)
    serializer_class = ChallengeSerializer
    http_method_names = ('options', 'head', 'get',)

    def get_serializer(self, *args, **kwargs):
        kwargs['context'] = {
            'request': self.request,
            'format': self.format_kwarg,
            'view': self
        }
        return self.serializer_class(*args, **kwargs)

    def get(self, request, challenge_pk):
        challenge = get_object_or_404(Challenge, pk=challenge_pk)
        return sendfile(request, challenge.picture.path, attachment=True)


class ChallengeViewSet(viewsets.ModelViewSet):
    """
    The current active challenge can be retrieved from `/api/challenges/current/`

    Setting the `exclude-done` query parameter to `true` will ignore Challenges in which the user has participated.

    `/api/challenges/current/?exclude_done=true`
    """
    queryset = Challenge.objects.all()
    serializer_class = ChallengeSerializer
    permission_classes = (IsAuthenticated,)
    http_method_names = ('options', 'head', 'get', 'post',)

    def list(self, request, *args, **kwargs):
        serializer = self.get_serializer(self.get_queryset(), many=True)
        return Response(serializer.data)

    def retrieve(self, request, pk=None, *args, **kwargs):
        serializer = self.get_serializer(get_object_or_404(self.get_queryset(), pk=pk))
        return Response(serializer.data)

    def create(self, request, *args, **kwargs):
        raise MethodNotAllowed(request.method)

    @list_route(methods=['get'])
    def current(self, request, *args, **kwargs):
        exclude_done = self.request.query_params.get('exclude-done', 'false')

        if exclude_done.lower() == 'true':
            challenge = Challenge.get_current(user=request.user)
        else:
            challenge = Challenge.get_current()

        if challenge is None:
            raise NotFound("No upcoming Challenge is available.")

        serializer = self.get_serializer(challenge)
        return Response(serializer.data)

    @detail_route(methods=['get', 'post'])
    def winner(self, request, pk=None, *args, **kwargs):
        # winner = get_object_or_404(Challenge, pk=pk).is_user_a_winner(request.user)
        participant = get_object_or_404(Participant, user=request.user, challenge_id=pk)

        if participant is None:
            raise NotFound("User did not participant in challenge.")

        winner_status = participant.get_winning_status()

        return Response(winner_status)

    @list_route(methods=['get'])
    def winning(self, request, *args, **kwargs):
        """Returns winning status, and badge and challenge if available"""
        # TODO: Filter by notification flag
        participant = Participant.objects.filter(user=request.user, is_winner=True, has_been_notified=False) \
            .order_by('date_completed') \
            .first()

        if participant is None:
            return Response({"available": False, "badge": None, "challenge": None})

        badge_settings = BadgeSettings.for_site(request.site)

        if badge_settings.challenge_win is None:
            raise NotFound('Challenge Badge not set up')

        # Create badge if it doesn't already exist
        site = Site.objects.get(is_default_site=True)
        user_badge = award_challenge_win(site, request.user, participant)

        data = OrderedDict()
        data['available'] = user_badge is not None and participant.challenge is not None
        data['badge'] = UserBadgeSerializer(instance=user_badge, context=self.get_serializer_context()).data
        data['challenge'] = ChallengeSerializer(instance=participant.challenge,
                                                context=self.get_serializer_context()).data
        return Response(data)

    @detail_route(methods=['post'])
    def notification(self, request, pk=None, *args, **kwargs):
        """Marks the participant as having received the winning notification"""
        participants = Participant.objects.filter(challenge_id=pk, user=request.user, has_been_notified=False)

        if participants is None:
            return Response(status=status.HTTP_204_NO_CONTENT)

        for p in participants:
            p.has_been_notified = True
            p.save()

        return Response(status=status.HTTP_204_NO_CONTENT)


# ================= #
# Challenge Entries #
# ================= #


class EntryViewSet(viewsets.ModelViewSet):
    queryset = Entry.objects.all()
    serializer_class = EntrySerializer
    http_method_names = ('options', 'head', 'get', 'post')

    def list(self, request, *args, **kwargs):
        serializer = self.get_serializer(self.get_queryset(), many=True)
        return Response(serializer.data)

    def retrieve(self, request, pk=None, *args, **kwargs):
        serializer = self.get_serializer(get_object_or_404(self.get_queryset(), pk=pk))
        return Response(serializer.data)

    def create(self, request, *args, **kwargs):
        serial = self.get_serializer(data=request.data, many=isinstance(request.data, list))
        if not serial.is_valid():
            return Response(data=serial.errors, status=400)
        serial.create(serial.validated_data)

        badge_settings = BadgeSettings.for_site(request.site)

        if badge_settings.challenge_entry is None:
            raise NotFound('Challenge entry badge not set up')

        participant_id = request.data['participant']

        participant = Participant.objects.get(user=request.user, id=participant_id)

        site = Site.objects.get(is_default_site=True)
        user_badge = award_entry_badge(site, request.user, participant)

        data = OrderedDict()
        data['badge'] = UserBadgeSerializer(instance=user_badge, context=self.get_serializer_context()).data
        data['data'] = serial.data

        return Response(data, status=status.HTTP_200_OK)


class ParticipantViewSet(viewsets.ModelViewSet):
    queryset = Participant.objects.all()
    lookup_field = 'pk'
    permission_classes = (IsAdminOrOwner, IsAuthenticated,)
    serializer_class = ParticipantRegisterSerializer

    def check_permissions(self, request):
        if not IsAuthenticated().has_permission(request, self):
            raise PermissionDenied("User must be authenticated")

    def check_object_permissions(self, request, obj):
        if not IsAdminOrOwner().has_object_permission(request, self, obj):
            raise PermissionDenied("Users can only access their own participant entries.")

    @list_route(methods=['get'])
    def check_registration(self, request, *args, **kwargs):
        self.check_permissions(request)
        q = request.query_params

        participant = get_object_or_404(Participant, user_id=request.user.id, challenge_id=q.get('challenge', None))
        self.check_object_permissions(request, participant)
        serial = self.get_serializer(participant)

        if serial.is_valid(raise_exception=True):
            return Response(data=serial.data)

    @list_route(methods=['post'])
    def register(self, request, *args, **kwargs):
        self.check_permissions(request)
        data = request.data
        data['user'] = request.user.id
        serial = self.get_serializer(data=data)

        if serial.is_valid(raise_exception=True):
            participant = serial.save()
            self.check_object_permissions(request, participant)
            serial = self.get_serializer(participant)
            return Response(data=serial.data)


class ParticipantAnswerViewSet(viewsets.ModelViewSet):
    queryset = ParticipantAnswer.objects.all()
    serializer_class = ParticipantAnswerSerializer
    http_method_names = ('options', 'head', 'get', 'post')

    def create(self, request, *args, **kwargs):
        serial = self.get_serializer(data=request.data, many=isinstance(request.data, list))
        if not serial.is_valid():
            return Response(data=serial.errors, status=400)
        serial.create(serial.validated_data)
        return Response(serial.data, status=201)


class ParticipantPictureViewSet(viewsets.ModelViewSet):
    # PARAM_USER_PK = 'user_pk'
    queryset = ParticipantPicture.objects.all()
    serializer_class = ParticipantPictureSerializer
    # permission_classes = (IsAdminOrOwner, IsAuthenticated,)
    http_method_names = ('options', 'head', 'get', 'post',)

    def check_object_permissions(self, request, obj):
        if not IsAdminOrOwner().has_object_permission(request, self, obj):
            raise PermissionDenied("Users can only access their own goal images.")

    def get_serializer_context(self):
        return {'request': self.request}

    def create(self, request, *args, **kwargs):
        participant_id = request.query_params.get('participant', None)
        request.data['participant'] = participant_id
        serial = self.get_serializer(data=request.data)
        # self.check_object_permissions(request, goal)
        if serial.is_valid(raise_exception=True):
            serial.save()
        return Response(status=status.HTTP_204_NO_CONTENT)

    def get(self, request, pk=None, *args, **kwargs):
        participantpicture = get_object_or_404(self.get_queryset(), pk=pk)
        # self.check_object_permissions(request, participantpicture)
        if not participantpicture.picture:
            raise ImageNotFound()
        return sendfile(request, participantpicture.picture.path)


class ParticipantImageView(GenericAPIView):
    queryset = Participant.objects.all()
    lookup_field = 'pk'
    lookup_url_kwarg = 'participant_pk'
    parser_classes = (FileUploadParser,)
    permission_classes = (IsAuthenticated,)
    serializer_class = ParticipantPictureSerializer

    def check_object_permissions(self, request, obj):
        if not IsAdminOrOwner().has_object_permission(request, self, obj):
            raise PermissionDenied("Users can only access their own participant images.")

    def post(self, request, participant_pk=None, *args, **kwargs):
        participant = get_object_or_404(Participant, pk=participant_pk)
        self.check_object_permissions(request, participant)
        print(participant)
        try:
            participant_picture = ParticipantPicture.objects.get(participant=participant)
        except ParticipantPicture.DoesNotExist:
            participant_picture = ParticipantPicture.objects.create(participant=participant)
        participant_picture.picture = request.FILES['file']
        participant_picture.save()

        badge_settings = BadgeSettings.for_site(request.site)

        if badge_settings.challenge_entry is None:
            raise NotFound('Challenge entry badge not set up')

        participant_id = participant_pk

        participant = Participant.objects.get(user=request.user, id=participant_id)
        challenge = participant.challenge

        site = Site.objects.get(is_default_site=True)
        user_badge = award_entry_badge(site, request.user, participant)

        data = OrderedDict()
        data['badge'] = UserBadgeSerializer(instance=user_badge, context=self.get_serializer_context()).data
        data['challenge'] = ChallengeSerializer(instance=challenge, context=self.get_serializer_context()).data

        return Response(data, status=status.HTTP_200_OK)

    def get(self, request, participant_pk=None, *args, **kwargs):
        participant = get_object_or_404(Participant, pk=participant_pk)
        self.check_object_permissions(request, participant)
        participant_picture = ParticipantPicture.objects.get(participant=participant)
        if not participant_picture.picture:
            raise ImageNotFound()
        return sendfile(request, participant_picture.picture)


class ParticipantFreeTextViewSet(viewsets.ModelViewSet):
    queryset = ParticipantFreeText.objects.all()
    serializer_class = ParticipantFreeTextSerializer
    permission_classes = (IsAuthenticated,)
    http_method_names = ('options', 'head', 'get', 'post', 'put')

    def check_permissions(self, request):
        if not IsAuthenticated().has_permission(request, self):
            raise PermissionDenied("User must be authenticated")

    def check_object_permissions(self, request, obj):
        if not IsAuthenticated().has_object_permission(request, self, obj):
            raise PermissionDenied("Users can only access their freeform entries.")

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid(raise_exception=True):
            serializer.save()

            badge_settings = BadgeSettings.for_site(request.site)

            if badge_settings.challenge_entry is None:
                raise NotFound('Challenge entry badge not set up')

            participant_id = request.data['participant']

            participant = Participant.objects.get(user=request.user, id=participant_id)

            site = Site.objects.get(is_default_site=True)
            user_badge = award_entry_badge(site, request.user, participant)

            data = OrderedDict()
            data['available'] = user_badge is not None
            data['badge'] = UserBadgeSerializer(instance=user_badge, context=self.get_serializer_context()).data
            data['data'] = serializer.data

            return Response(data, status=status.HTTP_201_CREATED)

    @list_route(methods=['get'])
    def fetch(self, request, *args, **kwargs):
        self.check_permissions(request)
        params = request.GET if hasattr(request, 'GET') else dict()
        challenge_id = int(params.get('challenge', None)) if params.get('challenge', None) else None

        # if user is staff and queries an ID, use specified ID
        if request.user.is_staff and params.get('user', None):
            user_id = int(params.get('user', None))
        # else use own ID
        else:
            user_id = request.user.id

        # participant must map user to challenge 1:1, so do a get if only one challenge
        result = self.get_queryset().filter(participant__user_id=user_id)
        if challenge_id:
            result = result.get(participant__challenge_id=challenge_id)
        serial = self.get_serializer(result, many=not challenge_id)

        return Response(data=serial.data)


# ==== #
# Tips #
# ==== #


class TipViewSet(viewsets.ModelViewSet):
    """Follow the article url to get the CMS page.
    """
    queryset = Tip.objects.all()
    serializer_class = TipSerializer
    permission_classes = (IsAuthenticated,)
    http_method_names = ('options', 'head', 'get', 'post')

    def get_queryset(self):
        queryset = super().get_queryset()
        return self.get_serializer_class().setup_prefetch_related(queryset)

    def list(self, request, *args, **kwargs):
        serializer = self.get_serializer(self.get_queryset().order_by('-first_published_at').filter(live=True), many=True)
        return Response(serializer.data)

    def retrieve(self, request, pk=None, *args, **kwargs):
        serializer = self.get_serializer(self.get_object())
        return Response(serializer.data)

    @list_route(methods=['get'])
    def favourites(self, request, *args, **kwargs):
        tips = self.get_queryset().filter(favourites__user_id=request.user.id,
                                          favourites__state=TipFavourite.TFST_ACTIVE,
                                          live=True).order_by('-first_published_at')
        serializer = self.get_serializer(tips, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @detail_route(methods=['post'])
    def favourite(self, request, pk=None, *args, **kwargs):
        tip = self.get_object()
        fav, created = TipFavourite.objects.get_or_create(
            user=request.user,
            tip=tip
        )
        if not created:
            fav.favourite()
            fav.save()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @detail_route(methods=['post'])
    def unfavourite(self, request, pk=None, *args, **kwargs):
        tip = self.get_object()
        try:
            fav = TipFavourite.objects.get(tip_id=tip.id, user_id=request.user.id)
            fav.unfavourite()
            fav.save()
        except TipFavourite.DoesNotExist:
            pass
        return Response(status=status.HTTP_204_NO_CONTENT)


# ===== #
# Goals #
# ===== #


class GoalViewSet(viewsets.ModelViewSet):
    """
    Endpoint for Goals and Transactions.

    Posting transactions to `/api/goals/{goal_pk}/transactions/` will not create duplicates, based on the `date` and
    `value`.

    Transactions are immutable and cannot be updated or deleted. When updating a Goal, transactions added to the
    `transactions` field are ignored when they exist, and created if they don't.
    """
    queryset = Goal.objects.all()
    serializer_class = GoalSerializer
    permission_classes = (IsAdminOrOwner, IsAuthenticated,)
    http_method_names = ('options', 'head', 'get', 'post', 'put', 'delete',)

    def list(self, request, *args, **kwargs):
        serializer = self.get_serializer(self.get_queryset()
                                         .filter(user_id=request.user.id, state=Goal.ACTIVE)
                                         .order_by('start_date'), many=True)
        return Response(serializer.data)

    def retrieve(self, request, pk=None, *args, **kwargs):
        goal = self.get_object()
        if not goal.is_active:
            raise NotFound('Goal has been deleted')
        serializer = self.get_serializer(goal)
        return Response(serializer.data)

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid(raise_exception=True):
            goal = serializer.save()

            user_badge = award_first_goal(request, serializer.instance)
            if user_badge is not None:
                goal.add_new_badge(user_badge)
                goal.save()

            return Response(self.get_serializer(goal).data, status=status.HTTP_201_CREATED)

    def update(self, request, pk=None, *args, **kwargs):
        goal = self.get_object()
        if not goal.is_active:
            raise NotFound('Goal has been deleted')
        serializer = self.get_serializer(goal, data=request.data)
        if serializer.is_valid(raise_exception=True):
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)

    def destroy(self, request, pk=None, *args, **kwargs):
        goal = self.get_object()
        goal.deactivate()
        goal.save()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @detail_route(methods=['post', 'get'])
    def transactions(self, request, pk=None, *args, **kwargs):
        goal = self.get_object()

        if request.method == 'POST':
            serializer = GoalTransactionSerializer(data=request.data, many=True)
            if serializer.is_valid(raise_exception=True):
                serializer.save(goal=goal)
                data = {
                    'new_badges': UserBadgeSerializer(instance=self.award_badges(request, goal),
                                                      many=True,
                                                      context=self.get_serializer_context()).data
                }
                return Response(data, status=status.HTTP_201_CREATED)

        elif request.method == 'GET':
            serializer = GoalTransactionSerializer(goal.transactions.all(), many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)

    @staticmethod
    def award_badges(request, goal):
        new_badges = [
            award_goal_done(request, goal),
            award_goal_halfway(request, goal),
            award_goal_week_left(request, goal),
            award_transaction_first(request, goal),
            award_week_streak(request.site, request.user, WEEK_STREAK_2),
            award_week_streak(request.site, request.user, WEEK_STREAK_4),
            award_week_streak(request.site, request.user, WEEK_STREAK_6),
            award_weekly_target_badge(request.site, request.user, WEEKLY_TARGET_2, goal),
            award_weekly_target_badge(request.site, request.user, WEEKLY_TARGET_4, goal),
            award_weekly_target_badge(request.site, request.user, WEEKLY_TARGET_6, goal)
        ]

        return [b for b in new_badges if b is not None]


class GoalImageView(GenericAPIView):
    queryset = Goal.objects.all()
    lookup_field = 'pk'
    lookup_url_kwarg = 'goal_pk'
    parser_classes = (FileUploadParser,)
    permission_classes = (IsAuthenticated,)
    serializer_class = GoalSerializer

    def check_object_permissions(self, request, obj):
        if not IsAdminOrOwner().has_object_permission(request, self, obj):
            raise PermissionDenied("Users can only access their own goal images.")

    def post(self, request, goal_pk=None, *args, **kwargs):
        goal = get_object_or_404(Goal, pk=goal_pk)
        self.check_object_permissions(request, goal)
        goal.image = request.FILES['file']
        goal.save()
        return Response(status=status.HTTP_204_NO_CONTENT)

    def get(self, request, goal_pk=None, *args, **kwargs):
        goal = get_object_or_404(Goal, pk=goal_pk)
        self.check_object_permissions(request, goal)
        if not goal.image:
            raise ImageNotFound()
        return sendfile(request, goal.image.path)


class GoalPrototypeView(viewsets.ModelViewSet):
    queryset = GoalPrototype.objects.all()
    serializer_class = GoalPrototypeSerializer
    permission_classes = (IsAuthenticated,)

    def list(self, request, pk=None, *args, **kwargs):
        serializer = self.get_serializer(self.get_queryset().filter(state=GoalPrototype.ACTIVE), many=True)

        return Response(serializer.data)

# ====== #
# Badges #
# ====== #

class BadgesView(GenericAPIView):
    def get(self, request, *args, **kwargs):
        queryset = Badge.objects.all()
        urls = []
        for badge in queryset:
            urls.append(request.build_absolute_uri(badge.image.file.url))

        return Response({
            'urls' :  urls
        })

# ============ #
# Achievements #
# ============ #

class AchievementsView(GenericAPIView):
    permission_classes = (IsAuthenticated,)

    def check_object_permissions(self, request, obj):
        if not IsUserSelf().has_object_permission(request, self, obj):
            raise PermissionDenied("Users can only access their own achievements.")

    def get(self, request, user_pk, *args, **kwargs):
        user = get_object_or_404(User, pk=user_pk)
        self.check_object_permissions(request, user)
        serializer = AchievementStatSerializer(instance=AchievementStat(user), context=self.get_serializer_context())
        return Response(data=serializer.data)


def badge_social_view(request, slug):
    """An HTML view to be used for sharing Badges as links"""
    badge = get_object_or_404(Badge, slug=slug, state=Badge.ACTIVE)
    return render(request, 'content/badge_social.html', context={'badge': badge})


############
# Feedback #
############

class FeedbackViewSet(viewsets.ModelViewSet):
    queryset = Feedback.objects.all()
    serializer_class = FeedbackSerializer
    http_method_names = ('options', 'head', 'post',)
    permission_classes = (IsAuthenticated,)

    def check_permissions(self, request):
        if not IsUserSelf().has_permission(request, self):
            raise PermissionDenied('Users can only post feedback as themselves or anonymously.')

    def create(self, request, *args, **kwargs):
        data = request.data
        if data.get('user', None) is not None:
            self.check_permissions(request)
        serial = self.get_serializer(data=data)
        if serial.is_valid(raise_exception=True):
            serial.save()
            return Response(serial.data)
