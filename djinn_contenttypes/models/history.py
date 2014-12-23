from django.db import models
from django.conf import settings
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes import generic


CREATED = 1
CHANGED = 2
PUBLISHED = 3
UNPUBLISHED = 4


STATUS_MAP = ["", "created", "changed", "published", "unpublished"]


class HistoryManager(models.Manager):

    def log(self, instance, status_flag, user=None, change_message=''):

        entry = self.model(
            user=user,
            object_id=instance.id,
            object_ct=ContentType.objects.get_for_model(instance),
            status_flag=status_flag,
            change_message=change_message)
        entry.save()

    def get_last(self, instance, *flags, **kwargs):

        _filter = {
            'object_id': instance.id,
            'object_ct': ContentType.objects.get_for_model(instance)}

        if flags:
            _filter['status_flag__in'] = flags

        # NB: ordering is already on -date, so get _first_ here!
        #
        try:
            if kwargs.get("as_flag"):
                return self.filter(**_filter).first().status_flag
            else:
                return self.filter(**_filter).first()
        except:
            return None

    def has_been(self, instance, *flags):

        _filter = {
            'object_id': instance.id,
            'object_ct': ContentType.objects.get_for_model(instance)}

        if flags:
            _filter['status_flag__in'] = flags

        return self.filter(**_filter).exists()

    def delete_instance_log(self, instance):

        _filter = {
            'object_id': instance.id,
            'object_ct': ContentType.objects.get_for_model(instance)}

        self.filter(**_filter).delete()


class History(models.Model):

    """ status history of content """

    date = models.DateTimeField(auto_now_add=True)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True)
    object_ct = models.ForeignKey(ContentType)
    object_id = models.PositiveIntegerField()
    content_object = generic.GenericForeignKey('object_ct', 'object_id')
    status_flag = models.PositiveSmallIntegerField()
    change_message = models.TextField(blank=True)

    objects = HistoryManager()

    def __unicode__(self):

        try:
            status = STATUS_MAP[self.status_flag]
        except:
            status = self.status_flag

        return "'%s' %s" % (self.content_object, status)

    class Meta:

        app_label = "djinn_contenttypes"
        ordering = ["-date"]
