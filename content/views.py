from rest_framework.renderers import JSONRenderer
from rest_framework import viewsets
from rest_framework.response import Response
from .models import Challenge
from.serializers import ChallengeSerializer
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
