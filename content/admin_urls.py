
from django.conf.urls import url


from .admin_views import participant_mark_read
from .admin_views import participant_mark_shortlisted
from .admin_views import participant_mark_winner


urlpatterns = [
    url(r'^mark-read/(?P<participant_pk>\d)/$', participant_mark_read, name='participant-mark-read'),
    url(r'^mark-shortlisted/(?P<participant_pk>\d)/$', participant_mark_shortlisted, name='participant-mark-shortlisted'),
    url(r'^mark-winner/(?P<participant_pk>\d)/$', participant_mark_winner, name='participant-mark-winner'),
]
