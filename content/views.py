from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework import viewsets
from rest_framework.decorators import list_route, detail_route
from rest_framework.exceptions import PermissionDenied
from rest_framework.generics import GenericAPIView
from rest_framework.parsers import FileUploadParser
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from sendfile import sendfile


from .exceptions import ImageNotFound
from .models import Challenge, Entry, Goal, ParticipantAnswer, ParticipantFreeText, ParticipantPicture, Tip, \
    TipFavourite
from .permissions import IsAdminOrOwner
from .serializers import ChallengeSerializer, EntrySerializer, GoalSerializer, GoalTransactionSerializer, \
    ParticipantAnswerSerializer, ParticipantFreeTextSerializer, ParticipantPictureSerializer, TipSerializer


class ChallengePictureView(GenericAPIView):
    permission_classes = (IsAuthenticated,)
    serializer_class = ChallengeSerializer

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
    http_method_names = ('options', 'head', 'get', 'post')

    def list(self, request, *args, **kwargs):
        serializer = self.get_serializer(self.get_queryset().filter(live=True), many=True)
        return Response(serializer.data)

    def retrieve(self, request, pk=None, *args, **kwargs):
        serializer = self.get_serializer(self.get_object())
        return Response(serializer.data)

    @list_route(methods=['get'])
    def favourites(self, request, *args, **kwargs):
        tips = self.get_queryset().filter(favourites__user_id=request.user.id,
                                          favourites__state=TipFavourite.TFST_ACTIVE,
                                          live=True)
        serializer = self.get_serializer(tips, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @detail_route(methods=['post'])
    def favourite(self, request, pk=None, *args, **kwargs):
        tip = self.get_object()
        fav = TipFavourite.objects.create(
            user=request.user,
            tip=tip
        )
        fav.save()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @detail_route(methods=['post'])
    def unfavourite(self, request, pk=None, *args, **kwargs):
        tip = self.get_object()
        try:
            fav = TipFavourite.objects.get(tip_id=tip.id)
            fav.unfavourite()
            fav.save()
        except TipFavourite.DoesNotExist:
            pass
        return Response(status=status.HTTP_204_NO_CONTENT)


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
    http_method_names = ('options', 'head', 'get', 'post', 'put',)

    def list(self, request, *args, **kwargs):
        serializer = self.get_serializer(self.get_queryset().filter(user_id=request.user.id), many=True)
        return Response(serializer.data)

    def retrieve(self, request, pk=None, *args, **kwargs):
        serializer = self.get_serializer(self.get_object())
        return Response(serializer.data)

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid(raise_exception=True):
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)

    def update(self, request, pk=None, *args, **kwargs):
        goal = self.get_object()
        serializer = self.get_serializer(goal, data=request.data)
        if serializer.is_valid(raise_exception=True):
            serializer.save()
            return Response(status=status.HTTP_200_OK)

    @detail_route(methods=['post', 'get'])
    def transactions(self, request, pk=None, *args, **kwargs):
        goal = self.get_object()

        if request.method == 'POST':
            #context = self.get_serializer_context()
            #context['goal'] = goal
            serializer = GoalTransactionSerializer(data=request.data, many=True)
            if serializer.is_valid(raise_exception=True):
                serializer.save(goal=goal)
                return Response(status=status.HTTP_204_NO_CONTENT)
        elif request.method == 'GET':
            serializer = GoalTransactionSerializer(goal.transactions.all(), many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)


class ParticipantPictureViewSet(viewsets.ModelViewSet):
    #PARAM_USER_PK = 'user_pk'
    queryset = ParticipantPicture.objects.all()
    serializer_class = ParticipantPictureSerializer
    #permission_classes = (IsAdminOrOwner, IsAuthenticated,)
    http_method_names = ('options', 'head', 'get', 'post',)

    def check_object_permissions(self, request, obj):
        if not IsAdminOrOwner().has_object_permission(request, self, obj):
            raise PermissionDenied("Users can only access their own goal images.")

    def get_serializer_context(self):
        return {'request': self.request}

    def create(self, request, *args, **kwargs):
        serial = self.get_serializer(data=request.data)
        #self.check_object_permissions(request, goal)
        if serial.is_valid(raise_exception=True):
            serial.save()
        return Response(status=status.HTTP_204_NO_CONTENT)

    def get(self, request, pk=None, *args, **kwargs):
        participantpicture = get_object_or_404(self.get_queryset(), pk=pk)
        #self.check_object_permissions(request, participantpicture)
        if not participantpicture.picture:
            raise ImageNotFound()
        return sendfile(request, participantpicture.picture.path)


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


class ParticipantFreeTextViewSet(viewsets.ModelViewSet):
    queryset = ParticipantFreeText.objects.all()
    serializer_class = ParticipantFreeTextSerializer
    http_method_names = ('options', 'head', 'get', 'post', 'put')

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid(raise_exception=True):
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
