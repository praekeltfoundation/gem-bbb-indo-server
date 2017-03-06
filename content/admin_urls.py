from django.conf.urls import url, include

from .admin_views import participant_mark_read, report_goal_exports, report_challenge_exports
from .admin_views import participant_mark_shortlisted
from .admin_views import participant_mark_winner

urlpatterns = [
    # Participants
    url(r'^participants/mark-read/(?P<participant_pk>\d+)/$', participant_mark_read, name='participant-mark-read'),
    url(r'^participants/mark-shortlisted/(?P<participant_pk>\d+)/$', participant_mark_shortlisted, name='participant-mark-shortlisted'),
    url(r'^participants/mark-winner/(?P<participant_pk>\d+)/$', participant_mark_winner, name='participant-mark-winner'),

    # Reports
    url(r'^reports/goals/$', report_goal_exports, name='reports-goals'),
    url(r'^reports/challenges/$', report_challenge_exports, name='reports-challenges')
]
