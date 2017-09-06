
from django.shortcuts import get_object_or_404
from django.http.response import JsonResponse

from .models import EndlineSurveySelectUser


# TODO: permission_required('survey.can_change') Decide on proper permission
def survey_mark_can_receive(request, user_id):
    survey_accessor = get_object_or_404(EndlineSurveySelectUser, pk=user_id)
    survey_accessor.receive_survey = not survey_accessor.receive_survey
    survey_accessor.save()
    return JsonResponse({})
