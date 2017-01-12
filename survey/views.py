
from rest_framework import status
from rest_framework.exceptions import ValidationError, MethodNotAllowed
from rest_framework.decorators import list_route, detail_route
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet

from .models import CoachSurvey, CoachSurveySubmission, CoachSurveyResponse
from .serializers import CoachSurveySerializer, CoachSurveyResponseSerializer


class CoachSurveyViewSet(ModelViewSet):
    queryset = CoachSurvey.objects.all()
    serializer_class = CoachSurveySerializer
    permission_classes = (IsAuthenticated,)
    # post required for `submission`, but implicitly not allowed for survey itself
    http_method_names = ('head', 'options', 'get', 'post')

    def get_queryset(self):
        queryset = super(CoachSurveyViewSet, self).get_queryset()
        return queryset.filter(live=True)

    def create(self, request, *args, **kwargs):
        raise MethodNotAllowed('POST')

    @detail_route(['post'])
    def submission(self, request, pk=None, *args, **kwargs):
        survey = self.get_object()
        # Leveraging form to validate fields
        form = survey.get_form(request.data, page=survey, user=request.user)
        if form.is_valid():
            survey.process_form_submission(form)
            return Response(status=status.HTTP_204_NO_CONTENT)
        else:
            raise ValidationError(form.errors)

    @list_route(['get'])
    def current(self, request, *args, **kwargs):
        survey = CoachSurvey.get_current(request.user)
        available = survey is not None

        return Response(CoachSurveyResponseSerializer(
                instance=CoachSurveyResponse(available, survey),
                context=self.get_serializer_context()
            ).data)