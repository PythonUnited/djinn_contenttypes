from django.forms import CharField
from django.template.defaultfilters import removetags


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
            return removetags(value, 'script')
        else:
            return None