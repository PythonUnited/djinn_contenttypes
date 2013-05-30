from settings import URN_SCHEMA
from pgcontent.utils import get_object_by_ctype_id


def has_permission(perm, user, obj):

    """ Check whether the user has the permisson on the object (or the
    objects' permission_authority)."""

    authority = getattr(obj, "permission_authority", obj)

    if not authority:
        return True

    return user.has_perm(perm, obj=authority)


def object_to_urn(object):

    return URN_SCHEMA % {'object_app': object.app_label,
                         'object_ctype': object.ct_name,
                         'object_id': object.id}


def urn_to_object(urn):

    """ Fetch the object for this URN. If not found, return None """

    parts = urn.split(":")
    
    obj = None

    try:
        obj = get_object_by_ctype_id(parts[3], parts[4], app_label=parts[2])
    except:
        pass

    return obj
