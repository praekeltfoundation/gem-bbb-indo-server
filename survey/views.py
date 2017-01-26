
import json

from rest_framework import status
from rest_framework.exceptions import ValidationError, MethodNotAllowed
from rest_framework.decorators import list_route, detail_route
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet

from .models import CoachSurvey, CoachSurveySubmission, CoachSurveyResponse, CoachSurveySubmissionDraft
from .serializers import CoachSurveySerializer, CoachSurveyResponseSerializer


class CoachSurveyViewSet(ModelViewSet):
    queryset = CoachSurvey.objects.all()
    serializer_class = CoachSurveySerializer
    permission_classes = (IsAuthenticated,)
    # POST and PUT methods are required for `submission` and `drafts`, but implicitly not allowed for survey itself
    http_method_names = ('head', 'options', 'get', 'post', 'put')

    def get_queryset(self):
        queryset = super(CoachSurveyViewSet, self).get_queryset()

        bot_conversation_type = CoachSurvey.get_conversation_type(self.request.query_params.get('bot-conversation', None))
        if bot_conversation_type is not None:
            queryset = queryset.filter(bot_conversation=bot_conversation_type)

        return queryset.filter(live=True)

    @staticmethod
    def pop_consent(data):
        return data.pop(CoachSurvey.CONSENT_KEY, CoachSurvey.ANSWER_NO).lower() == CoachSurvey.ANSWER_YES

    def create(self, request, *args, **kwargs):
        # Users shouldn't be able to create surveys themselves
        raise MethodNotAllowed('POST')

    def update(self, request, *args, **kwargs):
        # Users shouldn't be able to update surveys themselves
        raise MethodNotAllowed('PUT')

    @detail_route(['put'])
    def draft(self, request, pk=None, *args, **kwargs):
        """Drafts are used for tracking the user's progress through the survey."""
        survey = self.get_object()
        draft, created = CoachSurveySubmissionDraft.objects.get_or_create(user=request.user, survey=survey)
        draft.consent = CoachSurveyViewSet.pop_consent(request.data)
        form = survey.get_form(request.data, page=survey, user=request.user)
        if form.is_valid():
            draft.submission = json.dumps(form.cleaned_data)
            draft.save()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @detail_route(['post'])
    def submission(self, request, pk=None, *args, **kwargs):
        survey = self.get_object()
        consent = CoachSurveyViewSet.pop_consent(request.data)
        # Leveraging form to validate fields
        form = survey.get_form(request.data, page=survey, user=request.user)
        if form.is_valid():
            survey.process_consented_submission(consent, form)
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
