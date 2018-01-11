from django.forms import CharField
from sanitizer.templatetags.sanitizer import strip_filter


class NoScriptCharField(CharField):

    """
    Specific CharField that filters out <script>-tags.
    """

    def to_python(self, value):

        """
        Strips <script>-tags from the field.
        """

        if value:
            value = value.replace("\r\n", "\n")
            return strip_filter(value)
        else:
            return None
