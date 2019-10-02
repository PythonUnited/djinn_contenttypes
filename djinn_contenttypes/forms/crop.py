from django import forms
from django.conf import settings
from django.contrib.admin.templatetags import admin_static
from image_cropping.widgets import get_attrs


class DjinnCroppingMixin(object):

    cropping_field_name = None

    def __init__(self, *args, **kwargs):

        if not self.cropping_field_name:
            raise NotImplementedError("Form-classes using DjinnCroppingMixin "
                                      "must provide the name of the image "
                                      "field in image_field_name")

        super().__init__(*args, **kwargs)

        hidden_attrs = {}
        image_field = getattr(self.instance, self.cropping_field_name, None)
        if image_field:
            hidden_attrs = get_attrs(image_field.image, self.cropping_field_name)
            self.fields[self.cropping_field_name].widget.attrs.update({'hide_image': True})

        self.fields[self.cropping_field_name + '_hidden'] = forms.CharField(
            max_length=500,
            required=False,
            widget=forms.HiddenInput(
                attrs=hidden_attrs
            )
        )

    @property
    def extra_media(self):
        js = [
            "image_cropping/js/jquery.Jcrop.min.js",
            "js/image_cropping.js",
        ]
        js = [admin_static.static(path) for path in js]

        # if settings.IMAGE_CROPPING_JQUERY_URL:
        #     js.insert(0, settings.IMAGE_CROPPING_JQUERY_URL)

        css = [
            "image_cropping/css/jquery.Jcrop.min.css",
            "image_cropping/css/image_cropping.css",
        ]
        css = {'all': [admin_static.static(path) for path in css]}

        return forms.Media(css=css, js=js)
