
from collections import OrderedDict

from django.conf import settings
from rest_framework.views import exception_handler


def structured_exception_handler(exc, context):

    response = exception_handler(exc, context)
    errors_key = settings.REST_FRAMEWORK['NON_FIELD_ERRORS_KEY']

    detail = response.data.pop('detail', '')
    non_field_errors = response.data.pop(errors_key, [])

    if detail:
        non_field_errors.insert(0, detail)

    # Get non_field_errors for related models
    rel_errors = OrderedDict()
    field_errors = OrderedDict()
    for k, v in response.data.items():
        if type(v) is dict:
            rel_errors[k] = v.pop(errors_key, [])
            for field, errors in v.items():
                field_errors[k + '_' + field] = errors
        else:
            field_errors[k] = v

    response.data = OrderedDict()
    response.data['status_code'] = response.status_code
    response.data[errors_key] = non_field_errors
    response.data['rel_errors'] = rel_errors
    response.data['field_errors'] = field_errors

    return response
