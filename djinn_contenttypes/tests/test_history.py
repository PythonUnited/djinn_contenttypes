from django.test.testcases import TestCase
from django.db import models
from django.contrib.auth import get_user_model
from djinn_contenttypes.models.history import (
    History, CHANGED, CREATED, PUBLISHED, UNPUBLISHED)


class HistoryTest(TestCase):

    def setUp(self):

        news_model = models.get_model("djinn_news", "News")
        user_model = get_user_model()

        self.user = user_model.objects.create(username="bobdobalina")
        self.content = news_model.objects.create(
            changed_by=self.user,
            title="test news",
            creator=self.user)

    def test_log(self):

        self.assertTrue(CREATED,
                        History.objects.get_last(self.content).status_flag)

        History.objects.log(self.content, CHANGED)

        self.assertTrue(CHANGED,
                        History.objects.get_last(self.content).status_flag)

    def test_get_last(self):

        """ Some more elaborate testing, to find out about the published/
        unpublished status of content """

        History.objects.log(self.content, PUBLISHED)

        self.assertTrue(PUBLISHED,
                        History.objects.get_last(
                            self.content,
                            PUBLISHED, UNPUBLISHED).status_flag)

        History.objects.log(self.content, CHANGED)

        self.assertTrue(PUBLISHED,
                        History.objects.get_last(
                            self.content,
                            PUBLISHED, UNPUBLISHED).status_flag)

        History.objects.log(self.content, UNPUBLISHED)

        self.assertTrue(UNPUBLISHED,
                        History.objects.get_last(
                            self.content,
                            PUBLISHED, UNPUBLISHED).status_flag)

        History.objects.log(self.content, PUBLISHED)

        self.assertTrue(PUBLISHED,
                        History.objects.get_last(
                            self.content,
                            PUBLISHED, UNPUBLISHED).status_flag)

    def test_auto_cleanup(self):

        History.objects.log(self.content, PUBLISHED)

        self.content.delete()

        self.assertEquals(None, History.objects.get_last(self.content))
