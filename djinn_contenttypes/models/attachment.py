import os
from django.db import models
from django.conf import settings
from django.utils.translation import ugettext_lazy as _
from photologue.models import ImageModel
import magic


class Attachment(models.Model):

    title = models.CharField(_('title'), max_length=100, null=True, blank=True)

    @property
    def permission_authority(self):

        return None

    @property
    def _file(self):

        raise NotImplementedError

    @property
    def absolute_url(self):
        return os.path.join(settings.MEDIA_URL, self._file.name)

    @property
    def absolute_path(self):
        return self._file.path

    def mimetype(self, lexical=False):

        if lexical:
            magic.from_file(self._file.name)
        else:
            magic.from_file(self._file.name, mime=True)

    def __unicode__(self):
        if self.title:
            return u"%s" % self.title

        return u"%s" % self._file.name

    class Meta:
        abstract = True
        app_label = "djinn_contenttypes"


class ImgAttachment(Attachment, ImageModel):

    @property
    def _file(self):

        return self.image

    class Meta:
        app_label = "djinn_contenttypes"


class FileAttachment(Attachment):

    # This is not a typo.
    #
    ffile = models.FileField(upload_to='files')

    @property
    def _file(self):

        return self.ffile
