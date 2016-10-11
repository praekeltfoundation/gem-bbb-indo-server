from __future__ import absolute_import, unicode_literals

from django.conf import settings
from django.conf.urls import include, url
from django.contrib import admin

from search import views as search_views
from content import views as content_views
from wagtail.wagtailadmin import urls as wagtailadmin_urls
from wagtail.wagtailcore import urls as wagtail_urls
from wagtail.wagtaildocs import urls as wagtaildocs_urls


urlpatterns = [
    url(r'^django-admin/', include(admin.site.urls)),

    url(r'^admin/', include(wagtailadmin_urls)),
    url(r'^documents/', include(wagtaildocs_urls)),

    url(r'^search/$', search_views.search, name='search'),
    url(r'^challenges/?$', content_views.ChallengeViewSet.as_view({'get': 'list'})),
    url(r'^challenges/(?P<pk>[0-9]+)/?$', content_views.ChallengeViewSet.as_view({'get': 'retrieve'})),

    url(r'^tips/$', content_views.TipViewSet.as_view({'get': 'list'}), name='tip-list'),
    url(r'^tips/(?P<pk>[0-9]+)/$', content_views.TipViewSet.as_view({'get': 'retrieve'}), name='tip-detail'),

    url(r'', include(wagtail_urls)),
]

if settings.DEBUG:
    from django.conf.urls.static import static
    from django.contrib.staticfiles.urls import staticfiles_urlpatterns

    # Serve static and media files from development server
    urlpatterns += staticfiles_urlpatterns()
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
