
from django.utils.translation import ugettext_lazy as _
from rest_framework import status
from rest_framework.exceptions import APIException


class DuplicateSurveySubmissionError(APIException):
    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = _('Multiple survey submissions are not allowed.')
