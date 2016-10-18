"""Django settings for use within the docker container."""

from os import environ

from .base import *


# Disable debug mode

DEBUG = False

SECRET_KEY = environ.get('SECRET_KEY') or 'please-change-me'

PROJECT_ROOT = (
    environ.get('PROJECT_ROOT') or dirname(dirname(abspath(__file__))))

COMPRESS_OFFLINE = True

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': os.path.join(BASE_DIR, 'bimbingbung.db'),
    }
}

MEDIA_ROOT = join(PROJECT_ROOT, 'media')

STATIC_ROOT = join(PROJECT_ROOT, 'static')
