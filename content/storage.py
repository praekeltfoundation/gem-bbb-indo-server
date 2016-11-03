
from django.conf import settings
from django.core.files.storage import FileSystemStorage


class GoalImgStorage(FileSystemStorage):
    def __init__(self, location=settings.SENDFILE_ROOT, base_url=settings.SENDFILE_URL, **kwargs):
        super(GoalImgStorage, self).__init__(location=location, base_url=base_url, **kwargs)
