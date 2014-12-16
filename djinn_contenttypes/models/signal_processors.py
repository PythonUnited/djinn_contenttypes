from django.db.models.signals import pre_save
from django.dispatch import receiver
import django.dispatch
from djinn_contenttypes.models.publishable import PublishableContent
from djinn_contenttypes.utils import implements


unpublish = django.dispatch.Signal(providing_args=["instance"])


@receiver(pre_save)
def publishable_pre_save(sender, instance, **kwargs):

    """ Listen to any post_save, determine whether it is a publishable thing
    and what happend to publishing...
    """

    if implements(instance, PublishableContent):

        try:
            current_instance = instance.__class__.objects.get(pk=instance.pk)

            if current_instance.is_published and not instance.is_published:

                unpublish.send(sender, instance=instance)
        except:
            pass
