from django.db import models
from django.utils.translation import ugettext_lazy as _
from django.contrib.contenttypes.models import ContentType
from django.contrib.auth.models import User, Permission
from django.template.defaultfilters import slugify
import django
from djinn_contenttypes.models.swappablemodel_mixin import SwappableModelMixin

if django.VERSION < (1, 10):
    from django.core.urlresolvers import reverse
else:
    from django.urls import reverse
from pgauth.base import LocalRoleMixin, Role
from pgauth.models import UserGroup
from pgauth.settings import VIEWER_ROLE_ID
from djinn_contenttypes.models.sharing import SharingMixin
from djinn_contenttypes.models.relatable import RelatableMixin
from djinn_workflow.utils import get_state


class BaseContent(models.Model, LocalRoleMixin, SharingMixin, RelatableMixin,
                  SwappableModelMixin):

    """ All Djinn content extends this base class. Or should... """

    title = models.CharField(_('Title'), max_length=200)
    created = models.DateTimeField(_('Created'), auto_now_add=True)
    changed = models.DateTimeField(_('Changed'), auto_now=True)
    creator = models.ForeignKey(User, related_name='%(class)s_creator', on_delete=models.PROTECT)
    changed_by = models.ForeignKey(User, related_name='%(class)s_changed_by', on_delete=models.PROTECT)
    removed_creator_name = models.CharField(_('Creator naam'), max_length=100,
                                            blank=True, null=True)
    userkeywords = models.CharField(_('Keywords'), max_length=500,
                                    null=True, blank=True)
    parentusergroup = models.ForeignKey(
        UserGroup,
        related_name='%(class)s_parentusergroup',
        null=True, blank=True, on_delete=models.SET_NULL)
    is_tmp = models.BooleanField(_('Temporary'), default=False)

    # Create a temporary object during add?
    #
    create_tmp_object = False

    def get_cache_key(self):

        return "%s_%s_%s" % (self.app_label, self.ct_name, self.id)

    def save(self, *args, **kwargs):

        max_keywords = getattr(self, 'max_keywords', 10)

        if self.userkeywords:
            self.userkeywords = self.userkeywords.replace("'", '')
            kw_list = self.userkeywords.split(',')[:max_keywords]
            self.userkeywords = ",".join([kw.strip() for kw in kw_list])

        # 08-09-2020 overdragen compleet maken door ook de creator te zetten.
        # anders gaan berichten er op verkeerde naam uit...
        if self.id:
            # get_owner heeft alleen betekenis als het object al eens is opgeslagen
            owner = self.get_owner()
            if owner:
                self.creator = owner

        response = super(BaseContent, self).save(*args, **kwargs)

        if not self.get_owner():
            self.set_owner(self.creator)
        return response

    def __unicode__(self):

        return self.title

    __str__ = __unicode__

    @property
    def slug(self):

        dynamic_slug = slugify(self.title or '_new_%s_' % str(self.__class__))
        if not dynamic_slug:
            # als iemand een niet-sluggable karakter in title zet, dan is
            # dynamic_slug leeg. We zetten er dan tenminste een underscore in
            # ter voorkoming Nonetype excepties
            return "_"

        return dynamic_slug

    @property
    def created_as_isoformat(self):
        return self.created.isoformat()

    @property
    def ct_class(self):

        """ Use this method at your own peril... it's expensive"""

        return ContentType.objects.get_for_model(self.__class__)

    @property
    def ct_name(self):
        return self.__class__.__name__.lower()

    @property
    def app_label(self):

        try:
            return self._meta.app_label
        except:
            return self.__module__.split(".")[0]

    @property
    def ct_label(self):

        """ Display name """

        return _(self.__class__.__name__)

    @property
    def in_closed_group(self):

        # Checks for membership_type in UserGroup this content_item possibly is
        # placed in
        return self.parentusergroup and self.parentusergroup.is_closed

    @property
    def is_public(self):

        """ We're public iff:
            * not in a closed group
            * we have an id
            * we're not temporary
            * the state is not private
            * we're not deleted...
        """

        if not self.id:
            return False
        elif self.is_tmp:
            return False
        elif self.in_closed_group:
            return False
        elif get_state(self).name == "private":
            return False
        elif self.is_deleted:
            return False
        else:
            return True

    @property
    def is_deleted(self):

        try:
            self.__class__.objects.get(pk=self.id)
            _deleted = False
        except self.__class__.DoesNotExist:
            _deleted = True
        return self.created and _deleted

    @property
    def permission_authority(self):

        """ Return the permission authority for this object. This is
        usually the object itself, but in some cases, for example
        child objects like user profile phonenumbers, the check may be
        deferred to the parent object """

        return self

    @property
    def keywordslist(self):
        if self.userkeywords:
            return self.userkeywords.split(',')
        return []

    def pre_delete(self):

        """ May raise DeleteError """

        pass

    def delete(self):

        for lrole in self.get_local_roles():
            lrole.delete()

        self.pre_delete()

        return super(BaseContent, self).delete()

    def get_absolute_url(self):

        return reverse('%s_view_%s' % (self.app_label, self.ct_name),
                       kwargs={"slug": self.slug, "pk": str(self.id)})

    def get_local_roles(self, **kwargs):

        """ local roles are assigned as follows:
            1. if the content is public, the viewer role is given to all
            2. if the content is private, no one is allowed
            3. if the content is not public, but also not private,
               group members are given access.
        """

        roles = super(BaseContent, self).get_local_roles(**kwargs)

        if kwargs.get("as_role", False):

            if self.is_public:

                viewer = Role.objects.filter(
                    name=VIEWER_ROLE_ID).select_related()
                roles = roles | viewer

            elif get_state(self).name == "private" or (
                    hasattr(self, 'is_published') and not self.is_published):

                pass

            elif self.in_closed_group and kwargs.get("user", None):

                if kwargs['user'] in self.parentusergroup.members.all():

                    viewer = Role.objects.filter(
                        name=VIEWER_ROLE_ID).select_related()

                    roles = roles | viewer

        return roles

    @property
    def viewers(self):

        """ Return a list of all unique users and groups that can
        'view' this content."""

        _viewers = set()

        view = Permission.objects.get(codename="view")

        if self.is_public:
            _viewers.add("group_users")
        elif self.parentusergroup and self.is_published and get_state(
                self).name != "private":

            _viewers.add("group_%d" % self.parentusergroup.id)

        for lrole in self.get_local_roles():
            if view in lrole.role.permissions.all():

                try:
                    viewuser = lrole.user
                except User.DoesNotExist:
                    viewuser = None

                if viewuser:
                    _viewers.add("user_%s" % viewuser.username)
                else:
                    try:
                        viewusergroup = lrole.usergroup
                    except UserGroup.DoesNotExist:
                        viewusergroup = None

                    if viewusergroup:
                        _viewers.add("group_%d" % viewusergroup.id)

        return list(_viewers)

    @property
    def acquire_global_roles(self):

        """ Do we need to acquire global roles? Only if published... """

        if not self.is_public:
            return False
        else:
            return True

    class Meta:
        abstract = True


class FKContentMixin(object):

    """ Marker class for content that has a foreign key to some parent """
