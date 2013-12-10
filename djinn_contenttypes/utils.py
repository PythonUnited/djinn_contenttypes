from django.contrib.contenttypes.models import ContentType
from django.db.models.base import ModelBase
from djinn_contenttypes.registry import CTRegistry
from django.db.models import Model
from settings import URN_SCHEMA


def has_permission(perm, user, obj):

    """ Check whether the user has the permisson on the object (or the
    objects' permission_authority)."""

    authority = getattr(obj, "permission_authority", obj)

    if not authority:
        return True

    return user.has_perm(perm, obj=authority)


def object_to_urn(object):

    """ Create A URN for the given object """

    app_label = getattr(object, "app_label", object._meta.app_label)
    ct_name = getattr(object, object.ct_name,
                      object.__class__.__name__.lower())

    return URN_SCHEMA % {'object_app': app_label,
                         'object_ctype': ct_name,
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


def get_model_name(model):
    "Returns the Python model class for this type of content."
    if isinstance(model, Model) or isinstance(model, ModelBase):
        return model._meta.object_name.lower()
    return str(model)


def get_contenttype_by_ct_name(ct_name, app_label=None):
    if app_label is None:
        app_label = CTRegistry.get(ct_name)['app']

    return ContentType.objects.get(app_label=app_label,
                                   model=ct_name)


def get_contenttype_by_ctype(ctype, app_label=None):
    if app_label is None:
        app_label = CTRegistry.get(get_model_name(ctype))['app']

    return ContentType.objects.get(app_label=app_label,
                                   model=get_model_name(ctype))


def get_object_by_ctype(ctype, _id, app_label=None):

    content_type = get_contenttype_by_ctype(ctype, app_label=app_label)

    return content_type.get_object_for_this_type(id=_id)


def get_object_by_ctype_id(ctype_id, _id, app_label=None):

    ctype = CTRegistry.get(ctype_id)['class']

    return get_object_by_ctype(ctype, _id, app_label)
