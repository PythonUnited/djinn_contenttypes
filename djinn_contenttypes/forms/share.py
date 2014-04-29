from django import forms
from django.utils.translation import ugettext_lazy as _
from djinn_forms.widgets.share import ShareWidget


RECIPIENT_CHOICES = (
    ("followers", _("Colleagues that follow you")),
    ("group", _("Members of one or more groups")),
    ("user", _("One or more colleagues"))
)


class ShareField(forms.Field):

    def prepare_value(self, data):

        return []

    def clean(self, value):

        return value.get("add")


class ShareForm(forms.Form):

    # Translators: Content share form help
    help = _("Share this content")

    recipient = forms.CharField(
        label=_("Share with"), required=True,
        widget=forms.RadioSelect(choices=RECIPIENT_CHOICES)
    )

    group = ShareField(
        required=False,
        widget=ShareWidget(
            attrs={'searchfield': 'title_auto',
                   'content_types': ["djinn_profiles.groupprofile"]}
        )
    )

    user = ShareField(
        required=False,
        widget=ShareWidget(
            attrs={'searchfield': 'title_auto',
                   'content_types': ["djinn_profiles.userprofile"]}
        )
    )

    message = forms.CharField(
        label=_("Message to send with share"),
        max_length=200,
        widget=forms.Textarea(attrs={"class": "expand init_expansion",
                                     "cols": 100}),
        required=True
    )

    def clean(self):
        cleaned_data = super(ShareForm, self).clean()

        if cleaned_data.get("recipient", "") == "group" and \
           not cleaned_data.get("group"):

            raise forms.ValidationError(_("No group selected"))

        if cleaned_data.get("recipient", "") == "user" and \
           not cleaned_data.get("user"):
            raise forms.ValidationError(_("No colleague selected"))

        return cleaned_data
