from django.contrib.syndication.views import Feed


class DjinnFeed(Feed):

    def get_object(self, request, *args, **kwargs):

        super().get_object(request, *args, **kwargs)

        self.http_host = "%s://%s" % (
            request.scheme, request.META.get('HTTP_HOST', 'localhost:8000'))

    # item_link is only needed if NewsItem has no get_absolute_url method.
    # let op. De hostname:port combi komt uit django.Site (via admin)
    def item_link(self, item):
        # TODO: nadenken over detail pagina die niet achter inlog zit?
        # return reverse('djinn_news_view_news', args=[
        #     item.content_object.pk, item.content_object.slug])
        return "/"
