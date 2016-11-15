from os.path import join
from django.conf import settings
from django.core.files.storage import FileSystemStorage


class GoalImgStorage(FileSystemStorage):
    def __init__(self, location=settings.SENDFILE_ROOT, base_url=settings.SENDFILE_URL, **kwargs):
        super(GoalImgStorage, self).__init__(location=location, base_url=base_url, **kwargs)


class ParticipantPictureStorage(FileSystemStorage):
    def __init__(self,
                 location=join(settings.SENDFILE_ROOT, 'participant_pics'),
                 base_url=settings.SENDFILE_URL + 'participant_pics/',
                 **kwargs):
        super(ParticipantPictureStorage, self).__init__(location=location, base_url=base_url, **kwargs)


class ChallengeStorage(FileSystemStorage):
    def __init__(self,
                 location=join(settings.MEDIA_ROOT, 'challenge'),
                 base_url=settings.MEDIA_URL + 'challenge/',
                 **kwargs):
        super(ChallengeStorage, self).__init__(location=location, base_url=base_url, **kwargs)
