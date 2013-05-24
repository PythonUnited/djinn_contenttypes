from django.template import Library


register = Library()


@register.filter
def abbreviate(text, length=50):
    """
    Usage: {{ sometext|abbreviate:"50" }} Abbreviates given string if
    it is more than 'length' chars, and adds trailing dots.
    """

    if len(text) > length:
        return "%s..." % text[:length]
    return text
