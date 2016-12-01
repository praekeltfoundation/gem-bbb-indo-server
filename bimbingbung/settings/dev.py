from __future__ import absolute_import, unicode_literals

from .base import *

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = 'eh+r*5&#=5a_w!ln_5yux2_d69v73q71n6j!=+x16^6z48p^w$'


EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'


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
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'filters': ['require_debug_true'],
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
