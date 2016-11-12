from django.conf import settings
from django.core.files.storage import FileSystemStorage


class OverwriteStorage(FileSystemStorage):

    def get_available_name(self, name, max_length=None):
        self.delete(name)
        return name


class ProfileImgStorage(OverwriteStorage):
    def __init__(self, location=settings.SENDFILE_ROOT, base_url=settings.SENDFILE_URL, **kwargs):
        super(OverwriteStorage, self).__init__(location=location, base_url=base_url, **kwargs)
