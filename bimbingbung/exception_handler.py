
from collections import OrderedDict

from django.conf import settings
from rest_framework.views import exception_handler


def structured_exception_handler(exc, context):

    response = exception_handler(exc, context)

    detail = response.data.pop('detail', '')
    non_field_errors = response.data.pop(settings.REST_FRAMEWORK['NON_FIELD_ERRORS_KEY'], {})
    fields = response.data

    response.data = OrderedDict()
    response.data['detail'] = detail
    response.data[settings.REST_FRAMEWORK['NON_FIELD_ERRORS_KEY']] = non_field_errors
    response.data['field_errors'] = fields

    return response
