
from django.conf.urls import url


from .admin_views import participant_mark_read
from .admin_views import participant_mark_shortlisted


urlpatterns = [
    url(r'^mark-read/(?P<participant_pk>\d)/$', participant_mark_read, name='participant-mark-read'),
    url(r'^mark-shortlisted/(?P<participant_pk>\d)/$', participant_mark_shortlisted, name='participant-mark-shortlisted'),
]
