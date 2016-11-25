from __future__ import absolute_import, unicode_literals

from django.conf import settings
from django.conf.urls import include, url
from django.contrib import admin
from rest_framework.routers import DefaultRouter
from rest_framework.authtoken import views as framework_views

from search import views as search_views
from content import views as content_views
from users import views as user_views
from wagtail.wagtailadmin import urls as wagtailadmin_urls
from wagtail.wagtailcore import urls as wagtail_urls
from wagtail.wagtaildocs import urls as wagtaildocs_urls


router = DefaultRouter()
router.register(r'challenges', content_views.ChallengeViewSet, base_name='challenges')
router.register(r'entries', content_views.EntryViewSet, base_name='entries')
router.register(r'participantanswers', content_views.ParticipantAnswerViewSet, base_name='participantanswers')
router.register(r'participantfreetext', content_views.ParticipantFreeTextViewSet, base_name='participantfreetext')
router.register(r'participantpicture', content_views.ParticipantPictureViewSet, base_name='participantpicture')
router.register(r'tips', content_views.TipViewSet, base_name='tips')
router.register(r'goals', content_views.GoalViewSet, base_name='goals')
router.register(r'users', user_views.RegUserViewSet, base_name='users')

api_urls = [
    url(r'achievements/(?P<user_pk)/$', content_views.AchievementsView.as_view(), name='achievements'),
]

urlpatterns = [
    url(r'^django-admin/', include(admin.site.urls)),

    url(r'^admin/', include(wagtailadmin_urls)),
    url(r'^documents/', include(wagtaildocs_urls)),

    url(r'^search/$', search_views.search, name='search'),

    url(r'^api/token/', user_views.ObtainUserAuthTokenView.as_view(), name='token'),
    url(r'^api/challenge-image/(?P<challenge_pk>\d+)/$', content_views.ChallengeImageView.as_view(), name='challenge-image'),
    url(r'^api/goal-image/(?P<goal_pk>\d+)/$', content_views.GoalImageView.as_view(), name='goal-image'),
    url(r'^api/profile-image/(?P<user_pk>\d+)/$', user_views.ProfileImageView.as_view(), name='profile-image'),
    url(r'^api/', include(router.urls, namespace='api')),

    url(r'', include(wagtail_urls)),
]

if settings.DEBUG:
    from django.conf.urls.static import static
    from django.contrib.staticfiles.urls import staticfiles_urlpatterns

    # Serve static and media files from development server
    urlpatterns += staticfiles_urlpatterns()
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
