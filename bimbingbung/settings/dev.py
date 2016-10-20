from __future__ import absolute_import, unicode_literals

from .base import *

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = 'eh+r*5&#=5a_w!ln_5yux2_d69v73q71n6j!=+x16^6z48p^w$'


EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'


# SENDFILE settings

SENDFILE_BACKEND = 'sendfile.backends.development'
SENDFILE_ROOT = os.path.join(PROJECT_DIR, 'protected')
SENDFILE_URL = '/protected'


try:
    from .local import *
except ImportError:
    pass
