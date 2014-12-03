from django.test.testcases import TestCase
from djinn_contenttypes.models.relatable import RelatableMixin
from django.contrib.contenttypes.models import ContentType


class FakeContent(RelatableMixin):

    def __init__(self, _id):

        self.ct_class = ContentType.objects.get_for_model(ContentType)
        self.id = _id


RELATION = "SOME_RELATION"


class RelatableTest(TestCase):

    def setUp(self):

        self.source = FakeContent(1)
        self.target = FakeContent(2)

    def test_has_relation(self):

        self.assertFalse(self.source.has_relation(RELATION))
        self.assertFalse(self.target.has_relation(RELATION))

        self.source.add_relation(RELATION, self.target)

        # Ok, source should have a relation right now, target shouldn't...
        #
        self.assertTrue(self.source.has_relation(RELATION))
        self.assertFalse(self.target.has_relation(RELATION))

        # except when we ask for the inverse relation.
        #
        self.assertFalse(self.source.has_relation(RELATION, inverse=True))
        self.assertTrue(self.target.has_relation(RELATION, inverse=True))

        # Specifying the exact target should yield the same as without
        # target
        #
        self.assertTrue(self.source.has_relation(RELATION, self.target))
        self.assertFalse(self.source.has_relation(RELATION, self.source))

        # The target should have the inverse relation too!
        #
        self.assertTrue(self.target.has_relation(RELATION, inverse=True))
        self.assertTrue(self.target.has_relation(RELATION, inverse=True,
                                                 target=self.source))
