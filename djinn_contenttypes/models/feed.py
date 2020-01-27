from PIL import Image
from django.conf import settings
from django.db import models
from django.template.defaultfilters import striptags
from django.utils.translation import gettext_lazy as _
from django.utils.feedgenerator import Rss201rev2Feed
import os
import pyqrcode
import logging
from photologue.models import Photo, Watermark
from photologue.utils.watermark import apply_watermark
from easy_thumbnails.files import get_thumbnailer
from djinn_contenttypes.settings import FEED_HEADER_SIZE

log = logging.getLogger(__name__)

DESCR_FEED_MAX_LENGTH = getattr(settings, 'DESCR_FEED_MAX_LENGTH', 500)


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
    def has_feedimg(self):
        return self.use_default_image or \
               getattr(self, self.feed_bg_img_fieldname, False)

    @property
    def feedimg_too_small(self):
        img_field = getattr(self, self.feed_bg_img_fieldname, False)
        if not img_field:
            return False
        img = img_field.image
        if img.width < FEED_HEADER_SIZE.get(self.ct_name)[0] or \
                img.height < FEED_HEADER_SIZE.get(self.ct_name)[1]:
            return True
        return False

    @property
    def feedimg_selection_too_small(self):

        img_crop_field_value = getattr(self, self.feed_bg_img_crop_fieldname, False)
        if not img_crop_field_value:
            return False
        coords = img_crop_field_value.split(',')
        min_width = FEED_HEADER_SIZE.get(self.ct_name)[0]
        min_height = FEED_HEADER_SIZE.get(self.ct_name)[1]
        if int(coords[2])-int(coords[0]) < min_width or int(coords[3])-int(coords[1])<min_height:
            return True

        return False

    @property
    def feed_bg_img_url(self):
        feed_img = None
        feed_img_field = None

        if self.use_default_image:
            # Als plaatser bewust voor de stock-photo kiest, dan
            # de afbeelding die eventueel lokaal is ingesteld negeren
            slug = "%s_feed_placeholder" % self.__class__.__name__.lower()
            try:
                feed_img_field = Photo.objects.is_public().get(slug=slug)
                feed_img = Image.open(feed_img_field.image.file)
            except Exception as exc:
                log.error("stockphoto '%s' does not exist. "
                          "Upload in django-admin.photologue." % slug)

        if not feed_img_field:
            feed_img_field = getattr(self, self.feed_bg_img_fieldname, False)
        if not self.use_default_image and feed_img_field:
            img_crop_field_value = getattr(
                self, self.feed_bg_img_crop_fieldname, False)
            img_crop_field = self._meta.get_field(
                self.feed_bg_img_crop_fieldname)
            # with these options even lousy source images will be upscaled so
            # the overlay (watermark) will be applied correctly
            thumbnail_options = {
                'size': (img_crop_field.width, img_crop_field.height),
                'box': img_crop_field_value,
                'crop': "scale",
                'upscale': True,
                'detail': True,
            }

            # get the cropped version of img_field.image
            thumbnailer = get_thumbnailer(feed_img_field.image)
            feed_img = thumbnailer.get_thumbnail(thumbnail_options)
            if feed_img:
                # lot of feed_img juggling going on to be able to apply the watermark
                # to Photo instances as well as django-image-cropping images.
                feed_img = feed_img.image

        if feed_img:
            # see if a watermark is defined
            watermark = Watermark.objects.filter(name='feed_backgroundimage_watermark').first()
            if watermark:
                # if no watermark, return the url to the cropped image

                # TODO hier kan nog een check op het bestaan vd ge-watermark-te image.
                # TODO kan meteen worden teruggegeven.

                # apply the watermark
                watermark_image = Image.open(watermark.image.file)
                position = (feed_img.size[0]-watermark.image.width, 0)
                watermarked_thumbnail = apply_watermark(feed_img, watermark_image, position, opacity=1)

                # fix for Cannot write mode RGBA as JPEG
                watermarked_thumbnail = watermarked_thumbnail.convert("RGB")

                # insert "wm_" in the filename after last /
                sep_idx = feed_img_field.image.name.rindex("/") + 1
                wm_tn_name = feed_img_field.image.name[:sep_idx] + "wm_" + feed_img_field.image.name[sep_idx:]

                # save the watermarked image to this new filename
                wm_tn_filename = "/".join([settings.MEDIA_ROOT, wm_tn_name])
                watermarked_thumbnail.save(wm_tn_filename)

                feed_img_url = f"{settings.MEDIA_URL}{wm_tn_name}"

                return feed_img_url
            return feed_img.url

        # de achtergrondafbeelding mag ook leeg zijn...
        return None

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