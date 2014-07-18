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

        return data or {'add': [], 'rm': []}

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
        # Translators: share form group label
        label=_("Share with group"),
        required=False,
        widget=ShareWidget(
            attrs={'searchfield': 'title_auto',
                   # Translators: share user placeholder
                   'hint': _("Find group to share with"),
                   'content_type': ["djinn_profiles.groupprofile"]}
        )
    )

    user = ShareField(
        # Translators: share form user label
        label=_("Share with user"),
        required=False,
        widget=ShareWidget(
            attrs={'searchfield': 'title_auto',
                   # Translators: share user placeholder
                   'hint': _("Find user to share with"),
                   'content_type': ["djinn_profiles.userprofile"]}
        )
    )

    message = forms.CharField(
        # Translators: share form message label
        label=_("Message to send with share"),
        max_length=200,
        help_text="Maximaal 200 karakters",
        widget=forms.Textarea(
            attrs={"class": "expand count_characters init_expansion",
                   'data-maxchars': '200',
                   "cols": 100}),
        required=True
    )

    def clean(self):

        cleaned_data = super(ShareForm, self).clean()

        if cleaned_data.get("recipient", "") == "group" and \
           not cleaned_data.get("group"):

            # Translators: sharing group required
            msg = _("Selecting a group is required")

            self._errors["group"] = self.error_class([msg])

        if cleaned_data.get("recipient", "") == "user" and \
           not cleaned_data.get("user"):

            # Translators: sharing user required
            msg = _("Selecting a user is required")

            self._errors["user"] = self.error_class([msg])

        return cleaned_data

    
