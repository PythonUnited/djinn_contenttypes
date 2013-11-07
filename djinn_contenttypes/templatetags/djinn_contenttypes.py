# coding=utf-8
from django.template import Library


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

