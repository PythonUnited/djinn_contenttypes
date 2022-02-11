from djinn_contenttypes.models import Category

from haystack import indexes


class CategoryIndex(indexes.SearchIndex):

    def get_model(self):

        return Category