from django import forms
from djinn_contenttypes.models import ImgAttachment
from djinn_contenttypes.forms.base import MetaFieldsMixin


class ImgAttachmentForm(MetaFieldsMixin, forms.ModelForm):

    def clean_title(self):

        _title = self.cleaned_data.get('title')

        import pdb; pdb.set_trace()

        pass

    class Meta:
        model = ImgAttachment
        fields = ["title"]
