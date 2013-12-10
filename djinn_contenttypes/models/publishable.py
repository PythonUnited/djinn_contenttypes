from datetime import datetime
from django.db import models
from django.utils.translation import ugettext_lazy as _
from base import BaseContent


class PublishableContent(BaseContent):

    publish_from = models.DateTimeField(_('Publish from'), null=True,
                                        db_index=True,
                                        blank=True, default=None)
    publish_to = models.DateTimeField(_('Publish to'), null=True,
                                      db_index=True,
                                      blank=True, default=None)

    def is_published(self):

        """ Are we published? This is true iff:
        - not initial still
        - publish from is earlier than now
        - if pulish to is set, it is later than now
        """

        now = datetime.now()

        return not self.is_tmp and \
            (not self.publish_from or self.publish_from > now) and \
            (not self.publish_to or self.publish_to < now)

    @property
    def acquire_global_roles(self):

        if not self.is_published():
            return False
        else:
            return True

    class Meta:
        abstract = True
