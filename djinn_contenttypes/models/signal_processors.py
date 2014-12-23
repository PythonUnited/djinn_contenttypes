from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
import django.dispatch
from djinn_contenttypes.models.publishable import PublishableContent
from djinn_contenttypes.models.base import BaseContent
from djinn_contenttypes.models.history import (
    CREATED, CHANGED, PUBLISHED, UNPUBLISHED, History)
from djinn_contenttypes.utils import implements
from djinn_workflow.signals import state_change


unpublish = django.dispatch.Signal(providing_args=["instance"])
publish = django.dispatch.Signal(providing_args=["instance"])
created = django.dispatch.Signal(providing_args=["instance"])
changed = django.dispatch.Signal(providing_args=["instance"])


@receiver(post_save)
def basecontent_post_save(sender, instance, **kwargs):

    if kwargs.get('created', False) and implements(instance, BaseContent):
        History.objects.log(instance, CREATED, user=instance.creator)
        created.send(sender, instance=instance)
    elif implements(instance, BaseContent):
        History.objects.log(instance, CHANGED, user=instance.changed_by)
        changed.send(sender, instance=instance)


@receiver(post_delete)
def basecontent_post_delete(sender, instance, **kwargs):

    if implements(instance, BaseContent):
        History.objects.delete_instance_log(instance)


@receiver(state_change)
def publishable_state_change(sender, instance, **kwargs):

    publishable_post_save(sender, instance, **kwargs)


@receiver(post_save)
def publishable_post_save(sender, instance, **kwargs):

    """Publishable post save hook. If the content is new and 'is_public'
    is true:
    * if  there is no history of publishing, send publish with first_edition
      flag.
    * if the content does have a publishing history, omit this, but signal
      published.
    """

    if implements(instance, PublishableContent):

        if instance.is_public:

            changed = False

            if not History.objects.has_been(instance, PUBLISHED, UNPUBLISHED):

                publish.send(sender, instance=instance, first_edition=True)
                changed = True

            elif History.objects.get_last(
                    instance, PUBLISHED, UNPUBLISHED,
                    as_flag=True) == UNPUBLISHED:

                publish.send(sender, instance=instance)
                changed = True

            if changed:
                History.objects.log(instance, PUBLISHED,
                                    user=instance.changed_by)
                instance.__class__.objects.filter(pk=instance.pk).update(
                    publish_notified=True)

        else:
            if History.objects.get_last(
                    instance, PUBLISHED, UNPUBLISHED,
                    as_flag=True) == PUBLISHED:

                unpublish.send(sender, instance=instance)

                History.objects.log(instance, UNPUBLISHED,
                                    user=instance.changed_by)
