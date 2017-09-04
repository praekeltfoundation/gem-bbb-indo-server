from django.conf.urls import url, include

from .admin_views import participant_mark_read, report_goal_exports, report_challenge_exports, report_aggregate_exports, \
    report_index_page, report_survey_exports, feedback_mark_read, quiz_challenge_entries, report_budget_exports, \
    survey_mark_can_receive

from .admin_views import participant_mark_shortlisted
from .admin_views import participant_mark_winner

urlpatterns = [
    # Participants
    url(r'^participants/mark-read/(?P<participant_pk>\d+)/$', participant_mark_read, name='participant-mark-read'),
    url(r'^participants/mark-shortlisted/(?P<participant_pk>\d+)/$', participant_mark_shortlisted, name='participant-mark-shortlisted'),
    url(r'^participants/mark-winner/(?P<participant_pk>\d+)/$', participant_mark_winner, name='participant-mark-winner'),

    # Reports
    url(r'^reports/$', report_index_page, name='reports-index'),
    url(r'^reports/goals/$', report_goal_exports, name='reports-goals'),
    url(r'^reports/challenges/$', report_challenge_exports, name='reports-challenges'),
    url(r'^reports/aggregates/$', report_aggregate_exports, name='reports-aggregates'),
    url(r'^reports/surveys/$', report_survey_exports, name='reports-surveys'),
    url(r'^reports/budget/$', report_budget_exports, name='reports-budget'),

    # Custom quiz entry view
    url(r'^challenge/quizentries/$', quiz_challenge_entries, name='challenge-quizentries'),

    # Feedback controls
    url(r'^feedback/mark-read/(?P<feedback_pk>\d+)/$', feedback_mark_read, name='feedback-mark-read'),

    # Survey controls
    url(r'^survey/mark-can-receive/(?P<user_id>\d+)/$', survey_mark_can_receive, name='survey-mark-can-receive'),
]
