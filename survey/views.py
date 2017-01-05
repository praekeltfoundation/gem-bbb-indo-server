
from django.shortcuts import get_object_or_404
from rest_framework.decorators import detail_route
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet

from .models import CoachSurvey
from .serializers import CoachSurveySerializer


class CoachSurveyViewSet(ModelViewSet):
    queryset = CoachSurvey.objects.all()
    serializer_class = CoachSurveySerializer
    permission_classes = (IsAuthenticated,)
    http_method_names = ('head', 'options', 'get')

    def list(self, request, *args, **kwargs):
        serializer = self.get_serializer(self.get_queryset().filter(live=True), many=True)
        return Response(data=serializer.data)

    def retrieve(self, request, pk=None, *args, **kwargs):
        serializer = self.get_serializer(get_object_or_404(self.get_queryset(), live=True, pk=pk))
        return Response(data=serializer.data)
