from django.views.generic import DetailView
from djinn_contenttypes.utils import get_object_by_ctype_id


class FeedPreview(DetailView):

    template_name = 'djinn_contenttypes/feed_preview.html'

    def get_object(self):

        return get_object_by_ctype_id(self.kwargs['ctype'], self.kwargs['id'])

    def get_context_data(self, **kwargs):

        ctx = super().get_context_data(**kwargs)

        ctx['feed_name'] = "%s_feed_preview" % self.kwargs.get('ctype')

        return ctx