from __future__ import absolute_import, unicode_literals

from .base import *

DEBUG = False


# SENDFILE settings

SENDFILE_BACKEND = 'sendfile.backends.nginx'
SENDFILE_ROOT = os.environ.get('SENDFILE_ROOT', os.path.join(PROJECT_DIR, 'protected'))


try:
    from .local import *
except ImportError:
    pass
