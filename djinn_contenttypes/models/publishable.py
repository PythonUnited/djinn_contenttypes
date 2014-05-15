from datetime import datetime
from django.db import models
from django.utils.translation import ugettext_lazy as _
from base import BaseContent


class PublishableContent(BaseContent):

    """ Anything that is publishable should extend this class """

    publish_from = models.DateTimeField(_('Publish from'), null=True,
                                        db_index=True,
                                        blank=True, default=None)
    publish_to = models.DateTimeField(_('Publish to'), null=True,
                                      db_index=True,
                                      blank=True, default=None)
    publish_notified = models.BooleanField(
        _('Event sent'), default=False,
        help_text=_("Publish event is sent"))

    def is_published(self):

        """ Are we published? This is true iff:
          - not initial still
          - publish from is set and is earlier than now
          - if publish to is set, it is later than now
        """

        now = datetime.now()

        return not self.is_tmp and \
            (self.publish_from and self.publish_from <= now) and \
            (not self.publish_to or self.publish_to > now)

    def is_scheduled(self):

        """
        Are we scheduled to be published later?
        """

        now = datetime.now()
        return not self.is_tmp and \
            (self.publish_from and self.publish_from > now) and \
            (not self.publish_to or self.publish_to > now)

    @property
    def acquire_global_roles(self):

        """ Do we need to acquire global roles? Only if published... """

        if not self.is_published():
            return False
        else:
            return True

    class Meta:
        abstract = True
