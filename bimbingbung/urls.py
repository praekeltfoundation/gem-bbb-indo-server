from __future__ import absolute_import, unicode_literals

from django.conf import settings
from django.conf.urls import include, url
from django.contrib import admin
from rest_framework.routers import DefaultRouter
from rest_framework.authtoken import views as framework_views

from search import views as search_views
from content import views as content_views
from users import views as user_views
from survey import views as survey_views
from wagtail.wagtailadmin import urls as wagtailadmin_urls
from wagtail.wagtailcore import urls as wagtail_urls
from wagtail.wagtaildocs import urls as wagtaildocs_urls


router = DefaultRouter()
router.register(r'challenges', content_views.ChallengeViewSet, base_name='challenges')
router.register(r'entries', content_views.EntryViewSet, base_name='entries')
router.register(r'feedback', content_views.FeedbackViewSet, base_name='feedback')
router.register(r'goals', content_views.GoalViewSet, base_name='goals')
router.register(r'participantanswers', content_views.ParticipantAnswerViewSet, base_name='participantanswers')
router.register(r'participantfreetext', content_views.ParticipantFreeTextViewSet, base_name='participantfreetext')
router.register(r'participantpicture', content_views.ParticipantPictureViewSet, base_name='participantpicture')
router.register(r'participants', content_views.ParticipantViewSet, base_name='participants')
router.register(r'tips', content_views.TipViewSet, base_name='tips')
router.register(r'users', user_views.RegUserViewSet, base_name='users')
router.register(r'surveys', survey_views.CoachSurveyViewSet, base_name='surveys')
router.register(r'goal-prototypes', content_views.GoalPrototypeView, base_name='goal-prototypes')
router.register(r'notifications', content_views.CustomNotificationViewSet, base_name='notifications')
router.register(r'expense-categories', content_views.ExpenseCategoryView, base_name='expense-categories')
router.register(r'budgets', content_views.BudgetView, base_name='budgets')
router.register(r'expenses', content_views.ExpenseView, base_name='expenses')

api_urls = [
    # authentication endpoints
    url(r'token/', user_views.ObtainUserAuthTokenView.as_view(), name='token'),
    url(r'^security_question/', user_views.SecurityQuestionView.as_view(), name='security_question'),

    # image endpoints
    url(r'challenge-image/(?P<challenge_pk>\d+)/$', content_views.ChallengeImageView.as_view(), name='challenge-image'),
    url(r'goal-image/(?P<goal_pk>\d+)/$', content_views.GoalImageView.as_view(), name='goal-image'),
    url(r'participant-image/(?P<participant_pk>\d+)/$', content_views.ParticipantImageView.as_view(),
        name='participant-image'),
    url(r'profile-image/(?P<user_pk>\d+)/$', user_views.ProfileImageView.as_view(), name='profile-image'),

    # misc endpoints
    url(r'achievements/(?P<user_pk>\d+)/$', content_views.AchievementsView.as_view(), name='achievements'),

    #all badge url
    url(r'badge-urls/', content_views.BadgesView.as_view(), name='badge-urls'),

    # include viewset routes
    url(r'', include(router.urls)),
]

social_urls = [
    url(r'^badges/(?P<slug>[a-zA-Z0-9\-\_]+)/$', content_views.badge_social_view, name='badges-detail'),
]

urlpatterns = [
    url(r'^django-admin/', include(admin.site.urls)),

    url(r'^admin/', include(wagtailadmin_urls)),
    url(r'^documents/', include(wagtaildocs_urls)),

    url(r'^search/$', search_views.search, name='search'),

    url(r'^api/', include(api_urls, namespace='api')),
    url(r'^social/', include(social_urls, namespace='social')),

    url(r'', include(wagtail_urls)),
]

if settings.DEBUG:
    from django.conf.urls.static import static
    from django.contrib.staticfiles.urls import staticfiles_urlpatterns

    # Serve static and media files from development server
    urlpatterns += staticfiles_urlpatterns()
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
