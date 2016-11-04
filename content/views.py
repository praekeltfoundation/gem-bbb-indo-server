
from django.shortcuts import get_object_or_404
from rest_framework import viewsets
from rest_framework import status
from rest_framework.exceptions import PermissionDenied
from rest_framework.parsers import FileUploadParser
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.generics import GenericAPIView
from sendfile import sendfile

from .exceptions import InvalidQueryParam, ImageNotFound
from .models import Challenge, Entry, ParticipantAnswer, ParticipantFreeText, Tip, Goal
from .permissions import IsAdminOrOwner
from .serializers import ChallengeSerializer, EntrySerializer, ParticipantAnswerSerializer, \
    ParticipantFreeTextSerializer, TipSerializer, GoalSerializer


class ChallengeViewSet(viewsets.ModelViewSet):
    queryset = Challenge.objects.all()
    serializer_class = ChallengeSerializer
    http_method_names = ('options', 'head', 'get',)

    def list(self, request, *args, **kwargs):
        serializer = self.get_serializer(self.get_queryset(), many=True)
        return Response(serializer.data)

    def retrieve(self, request, pk=None, *args, **kwargs):
        serializer = self.get_serializer(get_object_or_404(self.get_queryset(), pk=pk))
        return Response(serializer.data)


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
        return Response(serial.data, status=201)


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


class TipViewSet(viewsets.ModelViewSet):
    """Follow the article url to get the CMS page.
    """
    queryset = Tip.objects.all()
    serializer_class = TipSerializer
    permission_classes = (IsAuthenticated,)
    http_method_names = ('options', 'head', 'get',)

    def list(self, request, *args, **kwargs):
        serializer = self.get_serializer(self.get_queryset().filter(live=True), many=True)
        return Response(serializer.data)

    def retrieve(self, request, pk=None, *args, **kwargs):
        serializer = self.get_serializer(get_object_or_404(self.get_queryset(), pk=pk))
        return Response(serializer.data)


class GoalViewSet(viewsets.ModelViewSet):
    PARAM_USER_PK = 'user_pk'
    queryset = Goal.objects.all()
    serializer_class = GoalSerializer
    permission_classes = (IsAdminOrOwner, IsAuthenticated,)
    http_method_names = ('options', 'head', 'get', 'post', 'put',)

    def get_user_pk(self, request):
        user_pk = getattr(request, 'query_params', {}).get(self.PARAM_USER_PK, None)

        if user_pk is None:
            return None
        else:
            try:
                return int(user_pk)
            except ValueError:
                raise InvalidQueryParam("User id was not a valid int")

    def get_queryset(self):
        """Optionally filter by User id."""
        queryset = self.queryset
        user_pk = self.request.query_params.get(self.PARAM_USER_PK, None)

        if not user_pk:
            return queryset

        try:
            user_pk = int(user_pk)
        except ValueError:
            raise InvalidQueryParam("User id was not a valid int")

        return queryset.filter(user__pk=user_pk)

    def list(self, request, *args, **kwargs):
        if not request.user.is_staff:
            user_pk = self.get_user_pk(request)
            if user_pk is None:
                raise PermissionDenied("Required query param %s" % self.PARAM_USER_PK)
            elif user_pk != request.user.pk:
                raise PermissionDenied("Restricted from accessing other Goals")

        serializer = self.get_serializer(self.get_queryset(), many=True)
        return Response(serializer.data)

    def retrieve(self, request, pk=None, *args, **kwargs):
        serializer = self.get_serializer(self.get_object())
        return Response(serializer.data)

    def create(self, request, *args, **kwargs):
        # TODO: Stricter permissions on User Ownership
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid(raise_exception=True):

            if serializer.validated_data.get('user', None) != request.user:
                raise PermissionError('Cannot create a goal for another user.')

            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)

    def update(self, request, pk=None, *args, **kwargs):
        goal = self.get_object()

        serializer = self.get_serializer(goal, data=request.data)
        if serializer.is_valid(raise_exception=True):
            serializer.save()
            return Response(status=status.HTTP_200_OK)


class GoalImageView(GenericAPIView):
    parser_classes = (FileUploadParser,)
    permission_classes = (IsAuthenticated,)
    serializer_class = GoalSerializer

    def check_object_permissions(self, request, obj):
        if not IsAdminOrOwner().has_object_permission(request, self, obj):
            raise PermissionDenied("Users can only access their own goal images.")

    def post(self, request, goal_pk):
        goal = get_object_or_404(Goal, pk=goal_pk)
        self.check_object_permissions(request, goal)
        goal.image = request.FILES['file']
        goal.save()
        serializer = self.get_serializer(get_object_or_404(Goal, pk=goal.pk))
        return Response(serializer.data, status.HTTP_201_CREATED)

    def get(self, request, goal_pk):
        goal = get_object_or_404(Goal, pk=goal_pk)
        self.check_object_permissions(request, goal)
        if not goal.image:
            raise ImageNotFound()
        return sendfile(request, goal.image.path)


class ParticipantFreeTextViewSet(viewsets.ModelViewSet):
    queryset = ParticipantFreeText.objects.all()
    serializer_class = ParticipantFreeTextSerializer
    http_method_names = ('options', 'head', 'get',)
