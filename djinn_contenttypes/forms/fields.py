from django.forms import CharField
from djinn_contenttypes.templatetags.djinn_contenttypes import pg_strip_filter


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
            return pg_strip_filter(value)
        else:
            return None
