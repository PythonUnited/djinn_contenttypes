import requests
from django.conf import settings
from django.contrib.contenttypes.models import ContentType
from django.db.models.base import ModelBase
from django.db.models import Model, get_model
from django.core import exceptions
from djinn_core.utils import implements
from djinn_contenttypes.registry import CTRegistry


def has_permission(perm, user, obj):

    """ Check whether the user has the permisson on the object (or the
    objects' permission_authority)."""

    authority = getattr(obj, "permission_authority", obj)

    if not authority:
        return True

    return user.has_perm(perm, obj=authority)


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


def json_serializer(obj):

    if implements(obj, Model):

        obj_data = {}

        for field in obj._meta.fields:
            try:
                obj_data[field.name] = str(field.value_from_object(obj))
            except:
                pass

        return str(obj_data)

    return "NOT SERIALIZABLE"


def get_comment_model():

    if settings.DJINN_COMMENT_MODEL:

        try:
            parts = settings.DJINN_COMMENT_MODEL.split('.')

            model = get_model(parts[0], parts[-1])
        except:
            raise exceptions.ImproperlyConfigured('Erroneous comment model')

        return model


def check_get_url(url, cookies=None):

    """ return http status for fetching this url """

    return requests.get(url, cookies=cookies,
                        allow_redirects=False).status_code
