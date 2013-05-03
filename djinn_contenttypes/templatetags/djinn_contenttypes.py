from django.template import Library


register = Library()


@register.filter
def abbreviate(text, length):
    """
    Usage: {{ sometext|abbreviate:"50" }} Abbreviates given string if
    it is more than 'length' chars, and adds trailing dots.
    """

    if len(text) > 50:
        return "%s..." % text[:50]
    return text
