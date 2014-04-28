from pgauth.base import Role
from pgauth.settings import VIEWER_ROLE_ID, EDITOR_ROLE_ID
from djinn_contenttypes.utils import get_object_by_ctype_id


class SharingMixin(object):

    def add_share(self, ctype, cid, mode):

        """ Add share to given ct, with mode """

        # Import runtime to prevent dependency hell.
        # TODO needs to be resolved obviously...
        #
        from pgevents.settings import SHARE_CONTENT
        from pgevents.events import Events

        if mode == 'viewer':
            role = Role.objects.get(name=VIEWER_ROLE_ID)
            mode = "bekijken"
        elif mode == 'editor':
            role = Role.objects.get(name=EDITOR_ROLE_ID)
            mode = "bewerken"

        tgt = get_object_by_ctype_id(ctype, cid)

        if getattr(tgt, "user", None):
            self.add_local_role(role, tgt.user)
            Events.send(SHARE_CONTENT,
                        self.get_owner(),
                        users=[tgt.user],
                        content=self, mode=mode)
        elif getattr(tgt, "usergroup", None):
            self.add_local_role(role, tgt.usergroup)

            Events.send(SHARE_CONTENT,
                        self.get_owner(),
                        users=tgt.usergroup.members.all(),
                        content=self, mode=mode)
        else:
            raise

    def rm_share(self, ctype, cid, mode):

        """ Remove share to given ct, with mode """

        if mode == 'viewer':
            role = Role.objects.get(name=VIEWER_ROLE_ID)
            mode = "bekijken"
        elif mode == 'editor':
            role = Role.objects.get(name=EDITOR_ROLE_ID)
            mode = "bewerken"

        tgt = get_object_by_ctype_id(ctype, cid)

        if getattr(tgt, "user", None):
            self.rm_local_role(role, tgt.user)
        elif getattr(tgt, "usergroup", None):
            self.rm_local_role(role, tgt.usergroup)
        else:
            raise

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
