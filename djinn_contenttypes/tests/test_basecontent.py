from datetime import datetime, timedelta
from django.test.testcases import TestCase
from django.db import models
from django.contrib.auth import get_user_model
from djinn_contenttypes.models.signal_processors import (
    unpublish, publish, created, changed)


class BaseContentTest(TestCase):

    def setUp(self):

        news_model = models.get_model("djinn_news", "News")
        user_model = get_user_model()

        self.user = user_model.objects.create(username="bobdobalina")
        self.content = news_model.objects.create(
            changed_by=self.user,
            title="test news",
            creator=self.user)

    def test_deleted(self):

        self.assertFalse(self.content.is_deleted)

        self.content.delete()

        self.assertTrue(self.content.is_deleted)

    def test_viewers(self):

        self.assertTrue("group_users" in self.content.viewers)

        self.content.set_owner(self.user)

        self.assertTrue("user_bobdobalina" in self.content.viewers)

        self.assertEquals(2, len(self.content.viewers))

        tomorrow = datetime.now() + timedelta(days=1)

        self.content.publish_from = tomorrow
        self.content.save()

        self.assertFalse("group_users" in self.content.viewers)

        self.assertTrue("user_bobdobalina" in self.content.viewers)

        self.assertEquals(1, len(self.content.viewers))

    def testlifecycle(self):

        callbacks = []

        def unpublish_callback(sender, instance, **kwargs):

            callbacks.append("unpublish")

        def publish_callback(sender, instance, **kwargs):

            if kwargs.get("first_edition"):
                callbacks.append("publish_first")
            else:
                callbacks.append("publish")

        def created_callback(sender, instance, **kwargs):

            callbacks.append("created")

        def changed_callback(sender, instance, **kwargs):

            callbacks.append("changed")

        unpublish.connect(unpublish_callback)
        publish.connect(publish_callback)
        created.connect(created_callback)
        changed.connect(changed_callback)

        tomorrow = datetime.now() + timedelta(days=1)

        news_model = models.get_model("djinn_news", "News")

        content = news_model.objects.create(
            changed_by=self.user,
            title="test news",
            creator=self.user)

        self.assertTrue("created" == callbacks[0])
        self.assertTrue("publish_first" == callbacks[1])
        self.assertEquals(2, len(callbacks))

        content.publish_from = tomorrow
        content.save()

        self.assertTrue("changed" == callbacks[-2])
        self.assertTrue("unpublish" == callbacks[-1])
        self.assertEquals(4, len(callbacks))

        content.publish_from = None
        content.save()

        self.assertTrue("changed" == callbacks[-2])
        self.assertTrue("publish" == callbacks[-1])
        self.assertEquals(6, len(callbacks))
