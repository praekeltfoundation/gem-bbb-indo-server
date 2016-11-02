
from django.shortcuts import get_object_or_404
from rest_framework import viewsets
from rest_framework.exceptions import ValidationError, PermissionDenied
from rest_framework.parsers import FileUploadParser
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.generics import GenericAPIView

from .exceptions import InvalidQueryParam
from .models import Challenge, Tip, Goal
from .permissions import IsAdminOrOwner
from .serializers import ChallengeSerializer, TipSerializer, GoalSerializer


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
    http_method_names = ('options', 'head', 'get', 'post',)

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
            if not getattr(request, 'query_params', {}).get(self.PARAM_USER_PK, None):
                raise PermissionDenied("Required query param %s" % self.PARAM_USER_PK)
            elif request.query_params.get(self.PARAM_USER_PK, None) != request.user.pk:
                raise PermissionDenied("Restricted from accessing other Goals")

        serializer = self.get_serializer(self.get_queryset(), many=True)
        return Response(serializer.data)

    def retrieve(self, request, pk=None, *args, **kwargs):
        serializer = self.get_serializer(self.get_object())
        return Response(serializer.data)

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(request.data)
        if serializer.is_valid(raise_exception=True):
            serializer.save()
            return Response(serializer.data)
