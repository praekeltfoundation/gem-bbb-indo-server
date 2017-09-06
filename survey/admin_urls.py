
from django.conf.urls import url

from .admin_views import survey_mark_can_receive


urlpatterns = [
    # Survey controls
    url(r'^survey/mark-can-receive/(?P<user_id>\d+)/$', survey_mark_can_receive, name='survey-mark-can-receive'),
]
