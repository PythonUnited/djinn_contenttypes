from django.db import models
from django.utils.translation import ugettext_lazy as _
from django.contrib.contenttypes.models import ContentType
from django.contrib.auth.models import User, Permission
from django.template.defaultfilters import slugify
from django.core.urlresolvers import reverse
from pgauth.base import LocalRoleMixin, Role
from pgauth.models import UserGroup
from pgauth.settings import VIEWER_ROLE_ID
from sharing import SharingMixin
from relatable import RelatableMixin


class BaseContent(models.Model, LocalRoleMixin, SharingMixin, RelatableMixin):

    """ All Djinn content extends this base class. Or should... """

    title = models.CharField(_('Title'), max_length=200)
    created = models.DateTimeField(_('Created'), auto_now_add=True)
    changed = models.DateTimeField(_('Changed'), auto_now=True)
    creator = models.ForeignKey(User, related_name='%(class)s_creator')
    changed_by = models.ForeignKey(User, related_name='%(class)s_changed_by')
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

        if self.userkeywords:
            self.userkeywords = self.userkeywords.replace("'", '')
            self.userkeywords = " ".join(self.userkeywords.split()[:10])
        super(BaseContent, self).save(*args, **kwargs)

    def __unicode__(self):

        return self.title

    @property
    def slug(self):

        return slugify(self.title)

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

        return self.parentusergroup and self.parentusergroup.profile and \
            self.parentusergroup.profile.is_closed

    @property
    def is_public(self):

        """ We are public if we are not in a closed group, and if we
        are published"""

        if self.in_closed_group:
            return False

        if not self.is_published():
            return False

        return True

    @property
    def permission_authority(self):

        """ Return the permission authority for this object. This is
        usually the object itself, but in some cases, for example
        child objects like user profile phonenumbers, the check may be
        deferred to the parent object """

        return self

    def is_published(self):
        '''
        By default everything is published
        (known to be overriden by PublishableBaseContent)
        '''
        return True

    @property
    def keywordslist(self):
        if self.userkeywords:
            return self.userkeywords.split()
        return []

    def pre_delete(self):

        """ May raise DeleteError """

        pass

    def delete(self):

        for lrole in self.get_local_roles():
            lrole.delete()

        return super(BaseContent, self).delete()

    def get_absolute_url(self):

        return reverse('%s_view_%s' % (self.app_label, self.ct_name),
                       kwargs={"slug": self.slug, "pk": str(self.id)})

    def get_local_roles(self, **kwargs):

        """ Override get_local_roles, so as to be able to add viewers """

        roles = super(BaseContent, self).get_local_roles(**kwargs)

        if kwargs.get("as_role", False):
            if self.is_public:

                viewer = Role.objects.filter(
                    name=VIEWER_ROLE_ID).select_related()
                roles = roles | viewer

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

        if self.parentusergroup and not self.ct_name == "groupprofile":
            if self.parentusergroup.membership_type != 1:
                _viewers.add("group_users")
            else:
                _viewers.add("group_%d" % self.parentusergroup.id)
        elif self.parentusergroup and self.ct_name == "groupprofile":
            _viewers.add("group_users")
        elif not self.parentusergroup:
            _viewers.add("group_users")

        return list(_viewers)

    class Meta:
        abstract = True


class FKContentMixin(object):

    """ Marker class for content that has a foreign key to some parent """
