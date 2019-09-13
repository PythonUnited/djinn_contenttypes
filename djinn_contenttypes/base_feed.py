import pyqrcode
import os
from django.conf import settings
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

    def get_qrcode_img_url(self, abs_url, content_object):

        qrcode_instance = pyqrcode.create(abs_url, error='Q')

        qrcode_filename = "qrcodes/%s_%s.png" % (
            content_object.ct_name, content_object.id)

        if not os.path.isdir(settings.MEDIA_ROOT + '/qrcodes'):
            os.mkdir(settings.MEDIA_ROOT + '/qrcodes')

        qrcode_instance.png("%s/%s" % (
            settings.MEDIA_ROOT, qrcode_filename), scale=6)

        qrcode_img_url = "%s%s%s" % (
                self.http_host, settings.MEDIA_URL, qrcode_filename)

        return qrcode_img_url