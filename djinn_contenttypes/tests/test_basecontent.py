from django.test.testcases import TestCase
from django.db import models
from django.contrib.auth import get_user_model
from djinn_contenttypes.models.base import BaseContent


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
