from datetime import datetime
from django.db import models
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes import generic
from django.utils.translation import ugettext_lazy as _


class Highlight(models.Model):

    """Hightlight given content. This can be used to set an additional
    period of highlighting, for instance to publish on the home page
    of the intranet

    """

    date_from = models.DateTimeField(
        _('Highlight from'), null=True,
        blank=True)

    date_to = models.DateTimeField(
        _('Highlight to'), null=True,
        blank=True)

    object_ct = models.ForeignKey(ContentType)
    object_id = models.PositiveIntegerField()
    content_object = generic.GenericForeignKey('object_ct', 'object_id')

    @property
    def human_date(self):

        delta = datetime.now() - self.date_from

        if delta.days == 0:
            return self.date_from.strftime('%H:%M')
        else:
            return self.date_from.strftime('%d-%m')

    def __unicode__(self):

        return "%s highlight" % self.content_object

    class Meta:

        app_label = "djinn_contenttypes"
        unique_together = ("object_ct", "object_id")
