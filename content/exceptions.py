
from django.utils.translation import ugettext_lazy as _
from rest_framework import status
from rest_framework.exceptions import APIException


class InvalidQueryParam(APIException):
    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = _('Query param was invalid.')
