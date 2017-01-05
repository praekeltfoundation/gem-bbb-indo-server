
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
    http_method_names = ('head', 'options', 'get', 'post')

    def get_queryset(self):
        queryset = super(CoachSurveyViewSet, self).get_queryset()
        return queryset.filter(live=True)

    @detail_route(['post'])
    def submission(self, request, pk=None, *args, **kwargs):
        return Response({})
