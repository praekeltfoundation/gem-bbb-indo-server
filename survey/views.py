
from rest_framework.viewsets import ModelViewSet
from rest_framework.response import Response

from .models import CoachSurvey
from .serializers import CoachSurveySerializer


class CoachSurveyViewSet(ModelViewSet):
    queryset = CoachSurvey.objects.all()
    serializer_class = CoachSurveySerializer

    def list(self, request, *args, **kwargs):
        serializer = self.get_serializer(self.get_queryset().filter(live=True), many=True)
        return Response(data=serializer.data)
