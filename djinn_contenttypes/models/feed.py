from django.conf import settings
from django.db import models
from django.template.defaultfilters import striptags
from django.utils.translation import gettext_lazy as _
from django.utils.feedgenerator import Rss201rev2Feed


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

    publish_for_feed = models.BooleanField(
        _("Toon op infoschermen"),
        default=False,
        help_text=_("Item tonen op infoscherm(en)")
    )

    description_feed = models.TextField(
        _("Infoscherm samenvatting"),
        null=True, blank=True,
        help_text=_("Samenvatting specifiek voor tonen op infoscherm(en)")
    )

    @property
    def keywords(self, sepchar=" + "):
        return sepchar.join(self.keywordslist)

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