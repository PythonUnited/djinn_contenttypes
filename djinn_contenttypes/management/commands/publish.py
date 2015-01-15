from datetime import datetime
from django.core.management.base import BaseCommand
from djinn_contenttypes.models.publishable import PublishableContent
from djinn_contenttypes.registry import CTRegistry
from django.utils import translation


class Command(BaseCommand):

    help = """Publish contenttypes if need be"""

    def handle(self, *args, **options):

        """Check contentitems that just have reached published state
        due to publish timestamp. We just call 'save' on the instance,
        and let the signal handlers take care of the rest. """

        now = datetime.now()
        translation.activate("nl_NL")

        for ctype in CTRegistry.list_types():

            model = CTRegistry.get_attr(ctype, "class")

            if issubclass(model, PublishableContent):

                for instance in model.objects.filter(publish_notified=False,
                                                     publish_from__lt=now):

                    instance.save()
