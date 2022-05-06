from django.conf.urls import url

from djinn_contenttypes.views.feedpreview import FeedPreview
from djinn_contenttypes.views.share import ShareView, ShareActivityView


urlpatterns = [

    url(r'^content/share/(?P<ctype>[\w]+)/(?P<id>[\d]+)/?$',
        ShareView.as_view(),
        name="djinn_contenttypes_share"),

    url(r'^content/share/(?P<activity_id>[\d]+)/?$',
        ShareActivityView.as_view(),
        name="djinn_contenttypes_share"),

    url(r'^gronet_v3/content/share/(?P<activity_id>[\d]+)/?$',
        ShareActivityView.as_view(
            template_name="gronet_v3/djinn_contenttypes/snippets/share.html"
        ),
        name="djinn_contenttypes_share_v3"),

    url(r'^content/preview/(?P<ctype>[\w]+)/(?P<id>[\d]+)/?$',
        FeedPreview.as_view(),
        name="djinn_contenttypes_preview"),
]
