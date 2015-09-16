from datetime import datetime
from django.core.management.base import BaseCommand
from django.db.models import Q
from djinn_contenttypes.models.publishable import PublishableContent
from djinn_contenttypes.registry import CTRegistry
from django.utils import translation


class Command(BaseCommand):

    help = """Publish contenttypes if need be"""

    def handle(self, *args, **options):

        """Check contentitems that are beyond the publish_to date.  We just
        call 'save' on the instance, and let the signal handlers take
        care of the rest.

        """

        now = datetime.now()
        translation.activate("nl_NL")

        for ctype in CTRegistry.list_types():

            model = CTRegistry.get_attr(ctype, "class")

            if issubclass(model, PublishableContent):

                for instance in model.objects.filter(
                        unpublish_notified=False,
                        publish_to__isnull=False).filter(
                            Q(publish_to__lt=now) | Q(publish_from__gt=now)):

                        # model.objects.filter(
                        # unpublish_notified=False,
                        # publish_to__isnull=False, publish_to__lt=now):

                    # be sure this unpublish is not handled again
                    instance.unpublish_notified = True

                    # prepare for a following publication of this instance
                    # print "un-publishing %s-%d" % (instance.ct_name, instance.id)
                    instance.publish_notified = False
                    instance.save()

                # clean up tenacious content...
                #
                for instance in model.objects.filter(
                        remove_after_publish_to=True,
                        publish_to__isnull=False, publish_to__lt=now):

                    instance.delete()
