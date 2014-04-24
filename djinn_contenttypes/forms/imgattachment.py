from django import forms
from djinn_contenttypes.models import ImgAttachment
from djinn_contenttypes.forms.base import MetaFieldsMixin


class ImgAttachmentForm(MetaFieldsMixin, forms.ModelForm):

    class Meta:
        model = ImgAttachment
        fields = ["title"]
