from django.conf.urls import url, include

from .admin_views import participant_mark_read, report_list_view
from .admin_views import participant_mark_shortlisted
from .admin_views import participant_mark_winner

# return [
#     url(r'^participants/', include(admin_urls, app_name='content', namespace='participants')),
#     url(r'^reports/', include(admin_urls, app_name='content', namespace='reports')),
# ]

urlpatterns = [
    # Participants
    url(r'^participants/mark-read/(?P<participant_pk>\d+)/$', participant_mark_read, name='participant-mark-read'),
    url(r'^participants/mark-shortlisted/(?P<participant_pk>\d+)/$', participant_mark_shortlisted, name='participant-mark-shortlisted'),
    url(r'^participants/mark-winner/(?P<participant_pk>\d+)/$', participant_mark_winner, name='participant-mark-winner'),

    # Reports
    url(r'^reports/$', report_list_view, name='reports')
]

# participant_urls = [
#     url(r'^mark-read/(?P<participant_pk>\d+)/$', participant_mark_read, name='participant-mark-read'),
#     url(r'^mark-shortlisted/(?P<participant_pk>\d+)/$', participant_mark_shortlisted,
#         name='participant-mark-shortlisted'),
#     url(r'^mark-winner/(?P<participant_pk>\d+)/$', participant_mark_winner, name='participant-mark-winner'),
# ]
#
# report_urls = [
#     url(r'^/$', report_list_view, name='reports')
# ]
