from django import forms
from django.utils.translation import ugettext_lazy as _
from pgauth.models import UserGroup
from pgcontent.fields import OwnerField, \
    RelatedContentField, SharesField
from pgcontent.widgets.content import RelatedContentWidget
from pgcontent.widgets.shares import SharesWidget
from pgcontent.widgets.owner import OwnerWidget
from pgcontent.settings import BASE_RELATEABLE_TYPES, get_relation_type_by_ctype
from djinn_contenttypes.utils import get_object_by_ctype_id


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

        for name in [name for name in self.fields if name in self._meta.fields]:
            yield self[name]


class BaseForm(PartialUpdateMixin, forms.ModelForm):

    title = forms.CharField(label=_("Title"),
                            max_length=255,
                            widget=forms.TextInput())

    class Meta:
        exclude = ["creator", "changed_by"]


class BaseContentForm(BaseForm):

    parentusergroup = forms.ModelChoiceField(label=_("Add to group"),
                                             required=False,
                                             queryset=UserGroup.objects.all())
    
    publish_from = forms.DateTimeField(label=_("Publish from"),
                                       required=False,
                                       widget=forms.DateTimeInput(
                attrs={'class': 'datetime'},
                format="%d-%m-%Y %H:%M"
                )                                       )
    
    publish_to = forms.DateTimeField(label=_("Publiceren till"),
                                     required=False,
                                     widget=forms.DateTimeInput(
                attrs={'class': 'datetime'},
                format="%d-%m-%Y %H:%M"
                ))
     
    userkeywords = forms.CharField(label=_("Keywords"),
                                   required=False,
                                   help_text=_("Enter keywords separated by spaces"),
                                   widget=forms.HiddenInput(
                attrs={'class': 'full',
                       'autocomplete': 'off'})
                                   )

    related = RelatedContentField(
        label=_("Related content"),
        required=False,
        widget=RelatedContentWidget(
            relation_types=BASE_RELATEABLE_TYPES,
            attrs={"add_link_label": _("Add link")}
            ))

    owner = OwnerField(label=_("Owner"),
                       required=False,
                       widget=OwnerWidget(
            attrs={"edit_link_label": _("Change owner")}
            ))

    shares = SharesField(label=_("Shares"),
                         widget=SharesWidget(
            attrs={"add_link_label": _("Add user or group")}
            ))

    def __init__(self, *args, **kwargs):

        super(BaseContentForm, self).__init__(*args, **kwargs)

        if 'related' in self.fields:
            self.fields['related'].widget.object = self.instance
        if 'owner' in self.fields:
            self.fields['owner'].widget.object = self.instance

        if 'shares' in self.fields:
            self.fields['shares'].widget.object = self.instance

        owner = self.instance.get_owner()

        if owner:
            self.fields['owner'].initial = "%s:%s" % (owner.profile.ct_name, 
                                                      owner.profile.id)

    def clean(self):

        try:
            if self.cleaned_data['publish_to'] < \
                    self.cleaned_data['publish_from']:
                self.cleaned_data['publish_to'] = None
        except:
            pass

        return self.cleaned_data

    def save(self, commit=True):

        """ Override save. This is needed for related add/rm actions and 
        ownership set """

        obj = super(BaseContentForm, self).save(commit=commit)

        # Related
        # TODO: move to widget
        #
        for ctype, cid in self.cleaned_data.get('related', {'rm': [],
                                                            'add': []})['rm']:
            tgt = get_object_by_ctype_id(ctype, cid)
            relation_type = get_relation_type_by_ctype(ctype)

            obj.rm_relation(relation_type, tgt)

        for ctype, cid in self.cleaned_data.get('related', {'rm': [],
                                                            'add': []})['add']:
            tgt = get_object_by_ctype_id(ctype, cid)
            relation_type = get_relation_type_by_ctype(ctype)

            obj.add_relation(relation_type, tgt)

        # Shares
        #
        for ctype, cid, mode in self.cleaned_data['shares']['rm']:
            obj.rm_share(ctype, cid, mode)

        for ctype, cid, mode in self.cleaned_data['shares']['add']:
            obj.add_share(ctype, cid, mode)

        if self.cleaned_data.get("owner", None):
            obj.set_owner(self.cleaned_data['owner'])

        return obj
