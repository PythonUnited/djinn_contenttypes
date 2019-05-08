from django.conf import settings
from django.db import models
from django.utils.translation import gettext_lazy as _

DESCR_FEED_MAX_LENGTH = getattr(settings, 'DESCR_FEED_MAX_LENGTH', 200)


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

    def save(self, *args, **kwargs):

        if not self.description_feed:
            txt = getattr(self, self.description_source_field, '')
            if txt:
                self.description_feed = txt[:DESCR_FEED_MAX_LENGTH]
                if len(txt) > DESCR_FEED_MAX_LENGTH:
                    self.description_feed += '...'

        return super().save(*args, **kwargs)

    class Meta:
        abstract = True