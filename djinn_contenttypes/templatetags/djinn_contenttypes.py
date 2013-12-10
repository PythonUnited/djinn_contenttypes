# coding=utf-8
from django.template import Library
from django.utils.translation import ugettext_lazy as _
from django.core.urlresolvers import reverse
from djinn_core.utils import implements as _implements


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
