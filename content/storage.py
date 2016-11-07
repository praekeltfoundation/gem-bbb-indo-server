from os.path import join
from django.conf import settings
from django.core.files.storage import FileSystemStorage


class GoalImgStorage(FileSystemStorage):
    def __init__(self, location=settings.SENDFILE_ROOT, base_url=settings.SENDFILE_URL, **kwargs):
        super(GoalImgStorage, self).__init__(location=location, base_url=base_url, **kwargs)


class ParticipantPictureStorage(FileSystemStorage):
    def __init__(self, location=None, base_url=None, **kwargs):
        if location is None:
            location = join(settings.SENDFILE_ROOT, 'challenge')
        if location is None:
            base_url = settings.SENDFILE_URL + 'challenge/'
        super(ParticipantPictureStorage, self).__init__(location=location, base_url=base_url, **kwargs)
