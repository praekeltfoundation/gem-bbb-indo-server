
from django.conf.urls import url


from .admin_views import participant_mark_read


urlpatterns = [
    url(r'^mark-read/(?P<participant_pk>\d)/$', participant_mark_read, name='participant-mark-read'),
]
