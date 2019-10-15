from django.conf import settings
from django.db import models
from django.template.defaultfilters import striptags
from django.utils.translation import gettext_lazy as _
from django.utils.feedgenerator import Rss201rev2Feed
from image_cropping.utils import get_backend
import os
import pyqrcode
import logging
from photologue.models import Photo

log = logging.getLogger(__name__)

DESCR_FEED_MAX_LENGTH = getattr(settings, 'DESCR_FEED_MAX_LENGTH', 200)


class MoreInfoFeedGenerator(Rss201rev2Feed):

    MORE_INFO_FIELDS = [
        'background_img_url', 'more_info_class', 'more_info_text',
        'more_info_qrcode_url', ]

    def get_more_info_fields(self):
        return self.MORE_INFO_FIELDS

    def add_item_elements(self, handler, item):
        super(MoreInfoFeedGenerator, self).add_item_elements(handler, item)
        for extrafield in self.get_more_info_fields():
            handler.addQuickElement(extrafield, item.get(extrafield, None))


class FeedMixin(models.Model):

    # name of the field that acts as source for description_field if it
    # is left empty
    # Can be overriden bij implementing classes
    description_source_field = 'text'
    feed_bg_img_fieldname = 'home_image'
    feed_bg_img_crop_fieldname = 'home_image_crop'

    publish_for_feed = models.BooleanField(
        _("Toon op infoschermen"),
        default=False,
        help_text=_("Item tonen op infoscherm(en)")
    )

    use_default_image = models.BooleanField(
        _("Standaard afbeelding gebruiken"),
        default=False,
        help_text=_("Gebruik de afbeelding die voor dit content-type als "
                    "standaardafbeelding is ingesteld.")
    )

    description_feed = models.TextField(
        _("Infoscherm samenvatting"),
        null=True, blank=True,
        help_text=_("Samenvatting specifiek voor tonen op infoscherm(en)")
    )

    def get_qrcode_img_url(self, abs_url, http_host=''):

        qrcode_instance = pyqrcode.create(abs_url, error='Q')

        qrcode_filename = "qrcodes/%s_%s.png" % (
            self.ct_name, self.id)

        if not os.path.isdir(settings.MEDIA_ROOT + '/qrcodes'):
            os.mkdir(settings.MEDIA_ROOT + '/qrcodes')

        qrcode_instance.png("%s/%s" % (
            settings.MEDIA_ROOT, qrcode_filename), scale=6)

        qrcode_img_url = "%s%s%s" % (
                http_host, settings.MEDIA_URL, qrcode_filename)

        return qrcode_img_url

    @property
    def get_qrcode_target_url(self):
        return self.get_absolute_url()

    def qrcode_img_url(self, http_host=''):
        target_url = self.get_qrcode_target_url
        if target_url.endswith('::'):
            # internal URL (or urn?). Remove the nasty characters
            target_url = target_url[:-2]
        if target_url.lower().startswith('http') or target_url.lower().startswith('//'):
            content_url = target_url
        else:
            content_url = "%s%s" % (http_host, target_url)

        url = self.get_qrcode_img_url(content_url, http_host=http_host)
        return url

    @property
    def keywords(self, sepchar=" + "):
        return sepchar.join(self.keywordslist)

    @property
    def more_info_text(self):
        info_text = ''
        if len(self.keywordslist) > 0:
            info_text = _("Zoek op: ") + " + ".join(self.keywordslist)
        return info_text

    @property
    def more_info_class(self):
        # May be overridden by subclass.
        return 'gronet'

    @property
    def feed_bg_img_url(self):
        feed_img_url = None

        if self.use_default_image:
            # Als plaatser bewust voor de stock-photo kiest, dan
            # de afbeelding die eventueel lokaal is ingesteld negeren
            slug = "%s_feed_placeholder" % self.__class__.__name__.lower()
            try:
                stockphoto = Photo.objects.is_public().get(slug=slug)
                return stockphoto.image.url
            except Exception as exc:
                log.error("stockphoto '%s' does not exist. "
                          "Upload in django-admin.photologue." % slug)

        img_field = getattr(self, self.feed_bg_img_fieldname, False)
        if img_field:
            img_crop_field_value = getattr(
                self, self.feed_bg_img_crop_fieldname, False)
            img_crop_field = self._meta.get_field(
                self.feed_bg_img_crop_fieldname)
            feed_img_url = get_backend().get_thumbnail_url(
                img_field.image,
                {
                    'size': (img_crop_field.width, img_crop_field.height),
                    'box': img_crop_field_value,
                    'crop': True,
                    'detail': True,
                }
            )
        # de achtergrondafbeelding mag ook leeg zijn...
        return feed_img_url

    def save(self, *args, **kwargs):
        txt = self.description_feed
        if not txt:
            txt = getattr(self, self.description_source_field, '')
        if txt:
            txt = striptags(txt)
            self.description_feed = txt[:DESCR_FEED_MAX_LENGTH]
            if len(txt) > DESCR_FEED_MAX_LENGTH:
                self.description_feed += '...'

        return super().save(*args, **kwargs)

    class Meta:
        abstract = True