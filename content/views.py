
from django.shortcuts import get_object_or_404
from rest_framework import viewsets
from rest_framework.request import Request
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from .models import Challenge, Entry, ParticipantAnswer, Tip
from .serializers import ChallengeSerializer, EntrySerializer, ParticipantAnswerSerializer, TipSerializer


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
