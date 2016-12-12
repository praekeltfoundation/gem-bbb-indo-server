from __future__ import absolute_import, unicode_literals

from .base import *

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = 'eh+r*5&#=5a_w!ln_5yux2_d69v73q71n6j!=+x16^6z48p^w$'


EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'


ALLOWED_HOSTS = [
    'localhost',
    '127.0.0.1',
    '10.0.2.2',  # Host address on Android Emulator
]


# SENDFILE settings

SENDFILE_BACKEND = 'sendfile.backends.development'
SENDFILE_ROOT = os.path.join(MEDIA_ROOT, 'protected')

LOGGING = {
    'disable_existing_loggers': False,
    'filters': {
        'require_debug_true': {
            '()': 'django.utils.log.RequireDebugTrue',
        }
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
    },
    'loggers': {
        'dooit': {
            'handlers': ['console'],
            'level': 'DEBUG',
            'propagate': True,
        },
    },
    'version': 1,
}


try:
    from .local import *
except ImportError:
    pass
