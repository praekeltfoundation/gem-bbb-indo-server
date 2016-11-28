
from django.utils.translation import ugettext_lazy as _
from rest_framework import status
from rest_framework.exceptions import APIException


class InvalidQueryParam(APIException):
    status_code = status.HTTP_400_BAD_REQUEST
    # Translators: Error message on API
    default_detail = _('Query param was invalid.')


class ImageNotFound(APIException):
    status_code = status.HTTP_404_NOT_FOUND
    # Translators: Error message on API
    default_detail = _('Image file not found')
