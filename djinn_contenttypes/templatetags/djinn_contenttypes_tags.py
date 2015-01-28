from django.template import Library
from django.utils.translation import ugettext_lazy as _
from djinn_workflow.utils import get_state


register = Library()


@register.simple_tag
def scheduled_line(obj):

    """ Return the object's 'scheduled' publishing """

    line = ""

    if obj.publish_from and obj.publish_to:

        line = _("From %(publish_from)s till %(publish_to)s" %
                 {'publish_from': obj.publish_from,
                  'publish_to': obj.publish_to})

    elif obj.publish_from:

        line = _("From %(publish_from)s" %
                 {'publish_from': obj.publish_from})

    elif obj.publish_to:

        line = _("Till %(publish_to)s" %
                 {'publish_to': obj.publish_to})

    return line


@register.simple_tag
def pub_classes(obj):

    """ publishing related CSS classes """

    classes = []

    if not obj.is_published:
        classes.append("unpublished")
    else:
        classes.append("published")

    if obj.is_scheduled:
        classes.append("scheduled")

    try:
        classes.append(get_state(obj).name)
    except:
        pass

    return " ".join(classes)
