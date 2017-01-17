"""Django settings for use within the docker container."""

from os import environ
from os.path import join

from .production import *
import raven


# Disable debug mode

DEBUG = False

SECRET_KEY = environ.get('SECRET_KEY') or 'please-change-me'

PROJECT_ROOT = (
    environ.get('PROJECT_ROOT') or dirname(dirname(abspath(__file__))))

COMPRESS_OFFLINE = True

ALLOWED_HOSTS = environ.get('ALLOWED_HOSTS', ['*'])

RAVEN_DSN = environ.get('RAVEN_DSN')
RAVEN_CONFIG = {'dsn': RAVEN_DSN} if RAVEN_DSN else {}


MEDIA_ROOT = join(PROJECT_ROOT, 'media')

STATIC_ROOT = join(PROJECT_ROOT, 'static')

LOGGING = {
    'disable_existing_loggers': False,
    'filters': {
        'require_debug_true': {
            '()': 'django.utils.log.RequireDebugTrue',
        }
    },
    'root': {
        'level': 'DEBUG',
        'handlers': ['sentry'],
    },
    'formatters': {
        'simple': {
            'format': '%(levelname)s %(message)s',
        },
        'verbose': {
            'format': '[%(asctime)s] %(levelname)s | %(module)s # %(message)s',
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'filters': ['require_debug_true'],
            'formatter': 'verbose',
            'level': 'DEBUG',
        },
        'sentry': {
            'level': 'DEBUG', # To capture more than ERROR, change to WARNING, INFO, etc.
            'class': 'raven.contrib.django.raven_compat.handlers.SentryHandler',
            #'tags': {'custom-tag': 'gem-sentry-tag'},
        },
    },
    'loggers': {
        'dooit': {
            'handlers': ['sentry'],
            'level': 'DEBUG',
            'propagate': True,
        },
        'django.db.backends': {
            'level': 'ERROR',
            'handlers': ['sentry'],
            'propagate': True,
        },
        'raven': {
            'level': 'DEBUG',
            'handlers': ['sentry'],
            'propagate': False,
        },
        'sentry.errors': {
            'level': 'DEBUG',
            'handlers': ['sentry'],
            'propagate': False,
        },
    },
    'version': 1,
}
