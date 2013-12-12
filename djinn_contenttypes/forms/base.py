from django import forms
from django.utils.translation import ugettext_lazy as _
from pgauth.models import UserGroup
from pgauth.settings import OWNER_ROLE_ID, EDITOR_ROLE_ID
from djinn_forms.fields.role import LocalRoleField, LocalRoleSingleField
from djinn_forms.fields.relate import RelateField
from djinn_forms.widgets.relate import RelateSingleWidget, RelateWidget
from djinn_forms.forms.relate import RelateMixin
from djinn_forms.widgets.datetimewidget import DateTimeWidget


class PartialUpdateMixin:

    def update(self, commit=True):

        """ Allow for updates of only the fields available in the form """

        for f in self.instance._meta.fields:
            if f.attname in self.fields:
                setattr(self.instance, f.attname,
                        self.cleaned_data[f.attname])
            if commit:
                try:
                    self.instance.save()
                except:
                    return False
            return self.instance


class MetaFieldsMixin(object):

    """ This mixin actually honours the fields setting of the meta info """

    def __iter__(self):

        for name in [name for name in self.fields if
                     name in self._meta.fields]:
            yield self[name]


class BaseForm(PartialUpdateMixin, forms.ModelForm):

    def __init__(self, *args, **kwargs):

        try:
            partial = kwargs.pop('partial')
        except:
            partial = False

        super(BaseForm, self).__init__(*args, **kwargs)

        if partial:
            self.fields = dict((fname, field) for fname, field in \
                                   self.fields.items() if \
                                   fname in self.data.keys())

    class Meta:
        pass


class BaseContentForm(BaseForm, RelateMixin):

    # Translators: contenttypes title label
    title = forms.CharField(label=_("Title"),
                            max_length=255,
                            widget=forms.TextInput())

    # Translators: contenttypes usergroup label
    parentusergroup = forms.ModelChoiceField(label=_("Add to group"),
                                             required=False,
                                             queryset=UserGroup.objects.all())

    publish_from = forms.DateTimeField(
        # Translators: contenttypes publish_from label
        label=_("Publish from"),
        required=False,
        widget=DateTimeWidget(
            attrs={'date_hint': _("Date"),
                   'time_hint': _("Time")}
            )
        )

    publish_to = forms.DateTimeField(
        # Translators: contenttypes publish_to label
        label=_("Publish from"),
        required=False,
        widget=DateTimeWidget(
            attrs={'date_hint': _("Date"),
                   'time_hint': _("Time")}
            )
        )

    userkeywords = forms.CharField(
        # Translators: contenttypes userkeywords label
        label=_("Keywords"),
        required=False,
        # Translators: contenttypes userkeywords help
        help_text=_("Enter keywords separated by spaces"),
        widget=forms.HiddenInput(
            attrs={'class': 'full',
                   'autocomplete': 'off'})
        )

    # TODO: Move this to relationfield in djinn_forms
    related = RelateField(
        #lambda x: "related_%s" % x.ct_name,
        "related_content",
        [],
        # Translators: contenttypes related label
        label=_("Related content"),
        required=False,
        widget=RelateWidget(
            attrs={'searchfield': 'title_auto',
                   #Translators: content type owner hint
                   'hint': _("Select related content ")
                   })
        )

    owner = LocalRoleSingleField(
        OWNER_ROLE_ID,
        ["pgprofile.userprofile"],
        # Translators: Contentype owner label
        label=_("Owner"),
        required=False,
        widget=RelateSingleWidget(
            attrs={'searchfield': 'title_auto',
                   #Translators: content type owner hint
                   'hint': _("Select a name")
                   })
        )

    shares = LocalRoleField(
        EDITOR_ROLE_ID,
        ["pgprofile.userprofile", "pgprofile.groupprofile"],
        # Translators: Contentype shares/editors label
        label=_("Editors"),
        # Translators: content shares help
        help_text=_("Select users or groups toshare editing role"),
        required=False,
        widget=RelateWidget(
            attrs={'searchfield': 'title_auto',
                   #Translators: content type owner hint
                   'hint': _("Select a user or group name ")
                   })
        )

    def __init__(self, *args, **kwargs):

        super(BaseContentForm, self).__init__(*args, **kwargs)
        self.init_relation_fields()

    def save(self, commit=True):

        res = super(BaseContentForm, self).save(commit=commit)
        self.save_relations()

        return res

    def clean(self):

        try:
            if self.cleaned_data['publish_to'] < \
                    self.cleaned_data['publish_from']:
                self.cleaned_data['publish_to'] = None
        except:
            pass

        return self.cleaned_data

    class Meta(BaseForm.Meta):
        exclude = ["creator", "changed_by"]
