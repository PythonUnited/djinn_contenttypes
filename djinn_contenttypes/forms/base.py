from django import forms
from django.utils.translation import ugettext_lazy as _
from djinn_forms.fields.share import ShareField
from djinn_forms.forms.share import ShareMixin
from djinn_workflow.utils import (
    get_workflow, get_state, apply_transition, set_state)
from pgauth.models import UserGroup
from pgauth.settings import OWNER_ROLE_ID, EDITOR_ROLE_ID, \
    PROFILE_TYPE_DEPARTMENT_ID
from djinn_forms.fields.role import LocalRoleSingleField
from djinn_forms.fields.relate import RelateField
from djinn_forms.fields.keyword import KeywordField
from djinn_forms.widgets.relate import RelateSingleWidget, RelateWidget
from djinn_forms.forms.relate import RelateMixin
from djinn_forms.widgets.datetimewidget import DateTimeWidget
from djinn_contenttypes import settings
from pgauth.util import get_usergroups_by_user


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
                   # Translators: content type owner hint
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
                   # Translators: content type owner hint
                   'hint': _("Select a user or group name ")
                   })
        )

    def __init__(self, *args, **kwargs):

        super(BaseSharingForm, self).__init__(*args, **kwargs)

        if not self.instance.get_owner(fail_silently=True) and self.user:
            self.fields['owner'].initial = self.user.profile
            self.fields['owner'].widget.initial = True


class BaseContentForm(BaseSharingForm):

    # Translators: contenttypes title label
    title = forms.CharField(label=_("Title"),
                            max_length=255,
                            widget=forms.TextInput())

    # Translators: contenttypes usergroup label
    parentusergroup = forms.ModelChoiceField(label=_("Add to group"),
                                             required=False,
                                             queryset=UserGroup.objects.none())


    publish_from = forms.DateTimeField(
        # Translators: contenttypes publish_from label
        label=_("Publish from"),
        # Translators: contenttypes publish_from help
        help_text=_("Enter a publish-from date and time"),
        required=False,
        widget=DateTimeWidget(
            attrs={'date_hint': _("Date"),
                   'time_hint': _("Time"),
                   'direct': True,
                   'date_format': settings.DEFAULT_DATE_INPUT_FORMAT
                   }
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
                   'time_hint': _("Time"),
                   'date_format': settings.DEFAULT_DATE_INPUT_FORMAT}
            )
        )

    state = forms.ChoiceField(
        # Translators: contenttypes status label
        label=_("Status"),
        # Translators: contenttypes publish_to help
        help_text=_("Enter a publish-to date and time"),
        choices=[],
        required=False,
        widget=forms.RadioSelect)

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

        self.fields['parentusergroup'].queryset = self._group_queryset()
        self.fields['parentusergroup'].choices = self._group_choices()

        self.fields['userkeywords'].show_label = True

        wf = get_workflow(self.instance)

        state = get_state(self.instance)
        if state.name != 'public':
            self.fields['state'].initial = "on"
        else:
            self.fields['state'].initial = None

        if not state:
            state = wf.initial_state

        self.fields['state'].choices = [
            (trans.name, trans.name) for trans in
            state.get_transitions(self.instance, self.user)]

        # If there is no parentusergroup in the instance, and the instance is
        # a temporary one, set the group to -1.
        # abuse the title field to assure it is really temporary.
        #
        if not self.instance.parentusergroup and self.instance.is_tmp and not self.instance.title:
            self.initial['parentusergroup'] = -1

        if 'description_feed' in self.fields:
            self.fields['description_feed'].widget.attrs.update({
                'placeholder': _(
                    "Geef hier de samenvatting voor infoschermen. Indien "
                    "niets ingevuld komt hier een ingekorte versie van het "
                    "tekst-veld."
                )
            })

    def _group_queryset(self):

        if self.user and self.user.is_superuser:
            groups = UserGroup.objects.all()
        elif self.user:
            groups = get_usergroups_by_user(self.user)
        else:
            groups = UserGroup.objects.none()

        groups = groups.exclude(profile_type=PROFILE_TYPE_DEPARTMENT_ID)

        # # if we already have a group set, add it.
        # #
        # if self.instance.parentusergroup:
        #     groups = groups | UserGroup.objects.filter(
        #         pk=self.instance.parentusergroup_id)
        #
        # # if the user is in a usergroup page and add permissions were granted:
        # if self.data.get('parentusergroup', False):
        #     groups = groups | UserGroup.objects.filter(
        #         pk=self.data.get('parentusergroup'))

        groups = groups.filter(is_system=False,
                               name__isnull=False).exclude(name="").distinct()
        return groups

    def _group_choices(self):

        """Populate group selector. This adds the special case '-1' for no
        selection made, so we can make sure the user needs to either
        select a group, or select 'no group'.
        """
        groups = self._group_queryset()

        groups_as_options = [(group.id, str(group)) for group in groups]
        # sorting must be done here since groups is a combination of 2 queries
        groups_as_options = sorted(groups_as_options, key=lambda x: x[1].lower())

        return [
            # First 2 choices always on top
            # Translators: djinn_contenttypes group make a choice label
            ("-1", _("Make a choice")),
            # Translators: djinn_contenttypes group no group label
            (("", _("Do not add to a group")))] + \
            groups_as_options

    def save(self, commit=True):

        res = super(BaseContentForm, self).save(commit=commit)

        # if the instance is created, set initial state, else apply
        # transition
        #
        # if self.instance.is_tmp and "state" in self.changed_data:
        if self.instance.is_tmp:
            if self.cleaned_data['state'] == "make_private":
                set_state(self.instance, "private")
            if "state" in self.changed_data:
                del self.changed_data[self.changed_data.index('state')]

        if commit and "state" in self.changed_data:

            apply_transition(self.instance, self.cleaned_data['state'])

        # Op de een of andere manier wordt de owner nergens gezet. Dan
        # maar hier
        if commit and 'owner' in self.cleaned_data.keys() and self.cleaned_data['owner']:
            self.instance.set_owner(self.cleaned_data['owner'].user)

        self.save_relations(commit=commit)
        self.save_shares(commit=commit)

        return res

    def clean(self):

        super(BaseContentForm, self).clean()

        _data = self.cleaned_data

        # Check publication sanity
        #
        if _data.get('publish_to') and _data.get('publish_from'):
            if _data.get('publish_to') < _data.get('publish_from'):
                raise forms.ValidationError(
                    _(u"Publish to date should be after publish from date"),
                    code='invalid')

        if _data.get('publish_from') == None and self.data.get('radiodirect') == "NotDirect":
            raise forms.ValidationError(
                (""),
                code='invalid')

        # Remove after publish requires the publish_to date to be set
        #
        if self.cleaned_data.get('remove_after_publish_to') and \
           not self.cleaned_data.get('publish_to'):
            raise forms.ValidationError(_(u"You must set the publish to date"))

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
