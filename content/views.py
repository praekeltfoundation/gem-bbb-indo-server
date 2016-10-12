from django.shortcuts import get_object_or_404
from rest_framework.renderers import JSONRenderer, BrowsableAPIRenderer
from rest_framework import viewsets
from rest_framework.response import Response
from .models import Challenge, Tip
from .serializers import ChallengeSerializer, TipSerializer
# Create your views here.


class ChallengeViewSet(viewsets.ModelViewSet):
    queryset = Challenge.objects.all()
    serializer_class = ChallengeSerializer
    renderer_classes = (JSONRenderer,)

    def list(self, request, *args, **kwargs):
        serializer = ChallengeSerializer(Challenge.objects.all(), many=True)
        return Response(JSONRenderer().render(serializer.data))

    def retrieve(self, request, pk=None, *args, **kwargs):
        serializer = ChallengeSerializer(Challenge.objects.get(pk=pk))
        return Response(JSONRenderer().render(serializer.data))


class TipViewSet(viewsets.ModelViewSet):
    queryset = Tip.objects.all()
    serializer_class = TipSerializer
    renderer_classes = (JSONRenderer, BrowsableAPIRenderer)

    def list(self, request, *args, **kwargs):
        serializer = self.get_serializer(self.get_queryset().filter(live=True), many=True)
        return Response(serializer.data)

    def retrieve(self, request, pk=None, *args, **kwargs):
        serializer = self.get_serializer(get_object_or_404(self.get_queryset(), pk=pk))
        return Response(serializer.data)
