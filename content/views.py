from django.shortcuts import get_object_or_404
from rest_framework import viewsets
from rest_framework.response import Response
from .models import Challenge, Tip
from .serializers import ChallengeSerializer, TipSerializer
# Create your views here.


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
    http_method_names = ('options', 'head', 'get',)

    def list(self, request, *args, **kwargs):
        serializer = self.get_serializer(self.get_queryset().filter(live=True), many=True)
        return Response(serializer.data)

    def retrieve(self, request, pk=None, *args, **kwargs):
        serializer = self.get_serializer(get_object_or_404(self.get_queryset(), pk=pk))
        return Response(serializer.data)
