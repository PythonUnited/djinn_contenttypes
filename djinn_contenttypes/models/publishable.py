from datetime import datetime
from django.db import models
from django.utils.translation import ugettext_lazy as _
from djinn_contenttypes.models.base import BaseContent


class PublishableMixin(object):

    @property
    def is_published(self):

        """The content is considered published if either dates are not set, or
        publish_from is earlier than now, and publish_to is later than
        now.  Note that this is not the same as 'is_public', since
        that also depends on visibility!

        """

        now = datetime.now()

        return ((not self.publish_from or self.publish_from < now)
                and
                (not self.publish_to or self.publish_to > now))

    @property
    def is_scheduled(self):

        """Determine whether one of date_from or date_to are set.  If so, we
        consider publishing to be 'scheduled', not considering the
        actual dates.

        """

        return self.publish_from or self.publish_to

    @property
    def is_public(self):

        """ Are we public? This is true iff:
          - not initial still
          - state is public
          - publish_from is empty or earlier than now
          - publish_to is empty or later than now
        """

        return (
            super(PublishableMixin, self).is_public
            and
            not self.is_tmp
            and
            self.is_published)


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
    unpublish_notified = models.BooleanField(
        _('Event sent'), default=False,
        help_text=_("Un-publish event is sent"))
    remove_after_publish_to = models.BooleanField(
        _('Remove the content ater publication to has past'), default=False)

    @property
    def publishing_date(self):

        """ If publish_from is set, use that, otherwise use created """

        return self.publish_from or self.created

    class Meta:
        abstract = True
