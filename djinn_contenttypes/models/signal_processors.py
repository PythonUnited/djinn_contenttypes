from datetime import datetime
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
import django.dispatch
from haystack import signal_processor
from djinn_contenttypes.models.publishable import PublishableContent
from djinn_contenttypes.models.base import BaseContent
from djinn_contenttypes.models.history import (
    CREATED, CHANGED, PUBLISHED, UNPUBLISHED, History)
from djinn_core.utils import implements
from djinn_workflow.signals import state_change


unpublish = django.dispatch.Signal(providing_args=["instance"])
publish = django.dispatch.Signal(providing_args=["instance"])
created = django.dispatch.Signal(providing_args=["instance"])
changed = django.dispatch.Signal(providing_args=["instance"])


@receiver(unpublish)
def basecontent_unpublish(sender, instance, **kwargs):

    """ If publishable content has the remove_after_publish_to flag set,
    and the publish_to date is in the past, remove the instance. """

    if implements(instance, PublishableContent):

        now = datetime.now()

        if instance.remove_after_publish_to:

            if instance.publish_to and instance.publish_to < now:

                instance.delete()


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

    """ After a state change, always call reindex given that a change of
    state usually means a change in permissions"""

    publishable_post_save(sender, instance, **kwargs)
    signal_processor.handle_save(sender, instance)


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

            # Have we not been published before?
            #

            if not History.objects.has_been(instance, PUBLISHED, UNPUBLISHED):

                publish.send(sender, instance=instance, first_edition=True)
                changed = True

            # Yes we have. But maybe currently we're unpublished?
            #
            elif History.objects.get_last(
                    instance, PUBLISHED, UNPUBLISHED,
                    as_flag=True) == UNPUBLISHED:

                publish.send(sender, instance=instance)
                changed = True

            if changed:
                History.objects.log(instance, PUBLISHED,
                                    user=instance.changed_by)
                instance.__class__.objects.filter(pk=instance.pk).update(
                    publish_notified=True, unpublish_notified=False)

        else:
            # We're are not public. So if the last state was
            # 'published', actively unpublish.
            #
            last_state = History.objects.get_last(
                instance, PUBLISHED, UNPUBLISHED,
                as_flag=True)

            if last_state == PUBLISHED:

                unpublish.send(sender, instance=instance)
                instance.__class__.objects.filter(pk=instance.pk).update(
                    unpublish_notified=True)

                # The instance may not be there anymore...
                #
                if not instance.is_deleted:
                    History.objects.log(instance, UNPUBLISHED,
                                        user=instance.changed_by)
