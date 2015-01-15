from datetime import datetime, timedelta
from django.test.testcases import TestCase
from django.db import models
from django.contrib.auth import get_user_model
from djinn_contenttypes.models.signal_processors import unpublish, publish


class PublishableTest(TestCase):

    def setUp(self):

        news_model = models.get_model("djinn_news", "News")
        user_model = get_user_model()

        self.user = user_model.objects.create(username="bobdobalina")
        self.content = news_model.objects.create(
            changed_by=self.user,
            title="test news",
            creator=self.user)

    def test_is_public(self):

        tomorrow = datetime.now() + timedelta(days=1)
        yesterday = datetime.now() - timedelta(days=1)

        # If nothing is said about publish_from or publish_to, the content is
        # public.
        #
        self.assertTrue(self.content.is_public)

        self.content.publish_from = tomorrow

        self.assertFalse(self.content.is_public)

        self.content.publish_from = yesterday

        self.assertTrue(self.content.is_public)

        self.content.publish_to = tomorrow

        self.assertTrue(self.content.is_public)

        self.content.publish_to = yesterday

        self.assertFalse(self.content.is_public)

    def test_is_published(self):

        tomorrow = datetime.now() + timedelta(days=1)
        yesterday = datetime.now() - timedelta(days=1)

        # If nothing is said about publish_from or publish_to, the content is
        # public.
        #
        self.assertTrue(self.content.is_published)

        self.content.publish_from = tomorrow

        self.assertFalse(self.content.is_published)

        self.content.publish_from = yesterday

        self.assertTrue(self.content.is_published)

        self.content.publish_to = tomorrow

        self.assertTrue(self.content.is_published)

        self.content.publish_to = yesterday

        self.assertFalse(self.content.is_published)

    def test_unpublish(self):

        tomorrow = datetime.now() + timedelta(days=1)

        self.assertTrue(self.content.is_public)

        def unpublish_callback(sender, instance, **kwargs):

            instance.publish_notified = False

        unpublish.connect(unpublish_callback)

        self.content.publish_notified = True
        self.content.publish_from = tomorrow
        self.content.save()

        self.assertFalse(self.content.publish_notified)

    def test_publish(self):

        tomorrow = datetime.now() + timedelta(days=1)
        yesterday = datetime.now() + timedelta(days=-1)
        signalled = []

        def publish_callback(sender, instance, **kwargs):

            signalled.append("published")

        publish.connect(publish_callback)

        self.assertTrue(self.content.is_published)

        self.content.publish_from = tomorrow
        self.content.save()

        self.assertFalse(self.content.is_published)

        self.content.publish_from = datetime.now()
        self.content.save()

        self.assertTrue(self.content.is_published)
        self.assertTrue(len(signalled) == 1 and signalled[0] == "published")

        self.content.publish_from = yesterday
        self.content.publish_to = yesterday
        self.content.save()

        self.assertFalse(self.content.is_published)

        self.content.publish_to = None
        self.content.save()

        self.assertTrue(self.content.is_published)
        self.assertTrue(len(signalled) == 2 and signalled[1] == "published")

    def test_remove_after_unpublish(self):

        yesterday = datetime.now() + timedelta(days=-1)
        tomorrow = datetime.now() + timedelta(days=1)

        self.content.publish_to = yesterday

        self.content.save()

        self.assertFalse(self.content.is_deleted)

        self.content.publish_to = tomorrow

        self.content.save()

        self.assertFalse(self.content.is_deleted)

        self.content.publish_to = yesterday
        self.content.remove_after_publish_to = True

        self.content.save()

        self.assertTrue(self.content.is_deleted)
