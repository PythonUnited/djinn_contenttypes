from django.contrib.contenttypes.models import ContentType
from django.contrib.auth.models import Permission
from pgauth.models import Role
from pgauth.settings import ADMIN_ROLE_ID

FEEDADMIN_ROLE_ID = "feed_admin"


def create_permissions(**kwargs):

    print("Creating/updating general content_type permissions (feed)")

    contenttype = ContentType.objects.get(
        app_label='auth',
        model='user')
    role_admin = Role.objects.get(name=ADMIN_ROLE_ID)
    role_feedadmin, created = Role.objects.get_or_create(
        name=FEEDADMIN_ROLE_ID)

    manage, created = Permission.objects.get_or_create(
        codename="manage_feeds",
        content_type=contenttype,
        defaults={'name': 'Manage feeds'})

    role_admin.add_permission_if_missing(manage)
    role_feedadmin.add_permission_if_missing(manage)
