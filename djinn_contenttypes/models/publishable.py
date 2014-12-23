from datetime import datetime
from django.db import models
from django.utils.translation import ugettext_lazy as _
from djinn_contenttypes.models.base import BaseContent


class PublishableMixin(object):

    @property
    def is_public(self):

        """ Are we published? This is true iff:
          - not initial still
          - state is public
          - publish_from is empty or earlier than now
          - publish_to is empty or later than now
        """

        now = datetime.now()

        return (
            super(PublishableMixin, self).is_public
            and
            (not self.is_tmp)
            and
            (not self.publish_from or self.publish_from < now)
            and
            (not self.publish_to or self.publish_to > now))


class PublishableContent(PublishableMixin, BaseContent):

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
    remove_after_publish_to = models.BooleanField(
        _('Remove the content ater publication to has past'), default=False)

    class Meta:
        abstract = True
