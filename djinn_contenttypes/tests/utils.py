from django.test.testcases import TestCase
from django.contrib.auth.models import User
from pgcontent.models import Article
from djinn_core.utils import object_to_urn, urn_to_object


class UtilsTest(TestCase):

    def setUp(self):

        super(UtilsTest, self).setUp()
        self.user = User.objects.create(username="bobdobalina",
                                        is_superuser=True)
        self.obj = Article.objects.create(title="Article 1",
                                          changed_by=self.user,
                                          creator=self.user)

    def test_object_to_urn(self):

        "urn:pu.in:%(object_app)s:%(object_ctype)s:%(object_id)s"

        self.assertEquals("urn:pu.in:pgcontent:article:%s" % self.obj.id,
                          object_to_urn(self.obj))

    def test_urn_to_object(self):

        self.assertEquals(
            self.obj,
            urn_to_object("urn:pu.in:pgcontent:article:%s" % self.obj.id))
