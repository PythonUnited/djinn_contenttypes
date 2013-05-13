from pgauth.base import Role
from pgauth.settings import VIEWER_ROLE_ID, EDITOR_ROLE_ID
from pgevents.settings import SHARE_CONTENT
from pgevents.events import Events
from djinn_contenttypes.utils import get_object_by_ctype_id


class SharingMixin(object):

    def add_share(self, ctype, cid, mode):

        """ Add share to given ct, with mode """

        if mode == 'viewer':
            role = Role.objects.get(name=VIEWER_ROLE_ID)
            mode = "bekijken"
        elif mode == 'editor':
            role = Role.objects.get(name=EDITOR_ROLE_ID)
            mode = "bewerken"

        tgt = get_object_by_ctype_id(ctype, cid)

        if ctype == "userprofile":
            self.add_local_role(role, tgt.user)
            Events.send(SHARE_CONTENT,
                        self.get_owner(),
                        users=[tgt.user],
                        content=self, mode=mode)
        elif ctype == "groupprofile":
            self.add_local_role(role, tgt.usergroup)
            
            Events.send(SHARE_CONTENT,
                        self.get_owner(),
                        users=tgt.usergroup.members.all(),
                        content=self, mode=mode)

    def rm_share(self, ctype, cid, mode):

        """ Remove share to given ct, with mode """

        if mode == 'viewer':
            role = Role.objects.get(name=VIEWER_ROLE_ID)
            mode = "bekijken"
        elif mode == 'editor':
            role = Role.objects.get(name=EDITOR_ROLE_ID)
            mode = "bewerken"

        tgt = get_object_by_ctype_id(ctype, cid)

        if ctype == "userprofile":
            self.rm_local_role(role, tgt.user)
        elif ctype == "groupprofile":
            self.rm_local_role(role, tgt.usergroup)

    @property
    def shares(self):
        return self.get_local_roles(
            role_filter=[EDITOR_ROLE_ID, VIEWER_ROLE_ID])

    @property
    def user_shares(self):
        return self.get_local_roles(
            role_filter=[EDITOR_ROLE_ID, VIEWER_ROLE_ID]).filter(
            user__isnull=False)

    @property
    def group_shares(self):
        return self.get_local_roles(
            role_filter=[EDITOR_ROLE_ID, VIEWER_ROLE_ID]).filter(
            usergroup__isnull=False)

