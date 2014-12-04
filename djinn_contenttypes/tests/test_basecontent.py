from datetime import datetime, timedelta
from django.test.testcases import TestCase
from django.db import models
from django.contrib.auth import get_user_model


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

        user_model = get_user_model()
        hankwilliams = user_model.objects.create(username="hankwilliams")

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
