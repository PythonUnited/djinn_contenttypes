from datetime import datetime
from django import forms
from django.utils.translation import ugettext_lazy as _
from djinn_forms.fields.share import ShareField
from djinn_forms.forms.share import ShareMixin
from pgauth.models import UserGroup
from pgauth.settings import OWNER_ROLE_ID, EDITOR_ROLE_ID
from djinn_forms.fields.role import LocalRoleSingleField
from djinn_forms.fields.relate import RelateField
from djinn_forms.fields.keyword import KeywordField
from djinn_forms.widgets.relate import RelateSingleWidget, RelateWidget
from djinn_forms.forms.relate import RelateMixin
from djinn_forms.widgets.datetimewidget import DateTimeWidget


class PartialUpdateMixin(object):

    partial_support = True

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

    user_support = True

    def __init__(self, *args, **kwargs):

        try:
            partial = kwargs.pop('partial')
        except:
            partial = False

        try:
            user = kwargs.pop("user")
        except:
            user = None

        super(BaseForm, self).__init__(*args, **kwargs)

        if partial:
            self.fields = dict((fname, field) for fname, field in
                               self.fields.items() if
                               fname in self.data.keys())

        self.user = user

    class Meta:
        exclude = ["creator", "changed_by"]


class BaseSharingForm(BaseForm, RelateMixin, ShareMixin):

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

    shares = ShareField(
        EDITOR_ROLE_ID,
        ["pgprofile.userprofile", "pgprofile.groupprofile"],
        # Translators: Contentype shares/editors label
        label=_("Editors"),
        # Translators: content shares help
        help_text=_("Select users or groups to share editing role"),
        required=False,
        widget=RelateWidget(
            attrs={'searchfield': 'title_auto',
                   #Translators: content type owner hint
                   'hint': _("Select a user or group name ")
                   })
        )


class BaseContentForm(BaseSharingForm):

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
        # Translators: contenttypes publish_from help
        help_text=_("Enter a publish-from date and time"),
        required=False,
        widget=DateTimeWidget(
            attrs={'date_hint': _("Date"),
                   'time_hint': _("Time")}
            )
        )

    publish_to = forms.DateTimeField(
        # Translators: contenttypes publish_to label
        label=_("Publish to"),
        # Translators: contenttypes publish_to help
        help_text=_("Enter a publish-to date and time"),
        required=False,
        widget=DateTimeWidget(
            attrs={'date_hint': _("Date"),
                   'time_hint': _("Time")}
            )
        )

    userkeywords = KeywordField(
        # Translators: contenttypes userkeywords label
        label=_("Keywords"),
        required=False,
        # Translators: contenttypes userkeywords help
        help_text=_("Enter keywords separated by spaces"),
    )

    related = RelateField(
        "related_content",
        [],
        # Translators: contenttypes related label
        label=_("Related content"),
        required=False,
        # Translators: Translators: contenttypes related hint
        help_text=_("Select related content"),
        widget=RelateWidget(
            attrs={'hint': _("Search relation"),
                   'searchfield': 'title_auto',
                   'template_name':
                   'djinn_forms/snippets/relatesearchwidget.html',
                   'search_url': '/content_search/', },
            )
        )

    def __init__(self, *args, **kwargs):

        super(BaseContentForm, self).__init__(*args, **kwargs)

        self.init_relation_fields()
        self.init_share_fields()

        self.fields['parentusergroup'].choices = self._group_choices()
        self.fields['userkeywords'].show_label = True

        # If there is no parentusergroup in the instance, and the instance is
        # a temporary one, set the group to -1.
        #
        if not self.instance.parentusergroup and self.instance.is_tmp:
            self.initial['parentusergroup'] = -1

    def _group_choices(self):

        """Populate group selector. This adds the special case '-1' for no
        selection made, so we can make sure the user needs to either
        select a group, or select 'no group'.
        """

        if self.user and self.user.is_superuser:
            groups = UserGroup.objects.all()
        elif self.user:
            groups = self.user.usergroup_set.all()
        else:
            groups = UserGroup.objects.none()

        # if we already have a group set, add it.
        #
        if self.instance.parentusergroup:
            groups = groups | UserGroup.objects.filter(
                pk=self.instance.parentusergroup.id)

        groups = groups.filter(is_system=False,
                               name__isnull=False).exclude(name="").distinct()

        return [
            # Translators: djinn_contenttypes group make a choice label
            ("-1", _("Make a choice")),
            # Translators: djinn_contenttypes group no group label
            (("", _("Do not add to a group")))] + \
            [(group.id, str(group)) for group in groups]

    def save(self, commit=True):

        res = super(BaseContentForm, self).save(commit=commit)

        self.save_relations(commit=commit)
        self.save_shares(commit=commit)

        return res

    def clean(self):

        # Check whether the 'save_as_concept' was used
        #
        if self.data.get("action") == "save":
            if not self.cleaned_data['publish_from']:
                self.cleaned_data['publish_from'] = datetime.now()
        elif self.data.get("action") == "save_as_concept":
            self.cleaned_data['publish_from'] = None
            self.cleaned_data['publish_to'] = None

        try:
            if self.cleaned_data['publish_to'] < \
                    self.cleaned_data['publish_from']:
                self.cleaned_data['publish_to'] = None
        except:
            pass

        return self.cleaned_data

    def clean_parentusergroup(self):

        """The parentusergroup requires some special attention: it is not
        required, but users need to make that choice explicitly. """

        group = self.cleaned_data.get('parentusergroup')

        if group == -1:
            if group == -1:
                # Translators: djinn_contenttypes parentusergroup required
                raise forms.ValidationError(_(u"Make a choice"))

        return group
