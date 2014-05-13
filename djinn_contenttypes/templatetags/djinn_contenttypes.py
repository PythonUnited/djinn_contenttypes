# coding=utf-8
"""
This filename should be renamed to something which is not equal to the
modulename.. it breaks the import from djinn_contenttypes
"""

from django.template import Library
from django.utils.translation import ugettext_lazy as _
from django.core.urlresolvers import reverse
from djinn_core.utils import implements as _implements
from djinn_core.utils import object_to_urn as obj_to_urn
from djinn_core.utils import HTMLTruncate


register = Library()


@register.filter
def abbreviate(text, length=50, truncate_str='...'):
    """
    Usage: {{ sometext|abbreviate:"50" }} Abbreviates given string if
    it is more than 'length' chars, and adds trailing dots.
    """

    if len(text) > length:
        return "%s%s" % (text[:length], truncate_str)
    return text


@register.filter
def abbreviate_hellip(text, length=50):
    """
    Usage: {{ sometext|abbreviate:"50" }} Abbreviates given string if
    it is more than 'length' chars, and adds trailing horizontal ellipsis.
    """

    return abbreviate(text, length, u'…')


@register.filter
def abbreviate_html(text, length=50):

    """ Break off the text content of 'text', ignoring the html tags, and
    making sure that no tags are cut off. """

    return HTMLTruncate(length).truncate(text)


@register.inclusion_tag('djinn_contenttypes/snippets/cancel_action.html')
def cancel_action(label=None):
    return {'label': label or _("Cancel")}


@register.inclusion_tag('djinn_contenttypes/snippets/delete_action.html')
def delete_action(obj, label=None):

    """ Determine delete URL and return button """

    return {'url': reverse("%s_delete_%s" % (obj.app_label,
                                             obj.ct_name),
                           kwargs={'pk': obj.id}),
            'label': label or _("Delete")}


@register.inclusion_tag('djinn_contenttypes/snippets/edit_action.html')
def edit_action(obj, label=None):

    """ Determine edit URL and return button """

    return {'url': reverse("%s_edit_%s" % (obj.app_label,
                                           obj.ct_name),
                           kwargs={'pk': obj.id}),
            'label': label or _("Edit")}


@register.filter
def edit_permission_id(obj):

    return "%s.change_%s" % (obj.app_label, obj.ct_name)


@register.filter
def delete_permission_id(obj):

    return "%s.delete_%s" % (obj.app_label, obj.ct_name)


@register.filter
def implements(instance, clazz):

    return _implements(instance, clazz)


@register.filter
def object_to_urn(obj):
    return obj_to_urn(obj)
