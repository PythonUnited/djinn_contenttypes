from django.conf.urls import patterns, url
from djinn_contenttypes.views.share import ShareView, ShareActivityView


urlpatterns = patterns(

    '',

    url(r'^content/share/(?P<ctype>[\w]+)/(?P<id>[\d]+)/?$',
        ShareView.as_view(),
        name="djinn_contenttypes_share"),

    url(r'^content/share/(?P<activity_id>[\d]+)/?$',
        ShareActivityView.as_view(),
        name="djinn_contenttypes_share"),
)
