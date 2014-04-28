from django.db import models
from django.utils.translation import ugettext_lazy as _
from djinn_contenttypes.utils import get_comment_model


class Commentable(models.Model):

    """
    Contains methods that apply to content for which you can add
    'Reacties' Comments do not use the SimpleRelation type, but are
    connected to content using CommentRelation
    """

    comments_enabled = models.BooleanField(_("Collega's kunnen reageren"),
                                           default=1)

    @property
    def comment_model(self):

        return get_comment_model()

    def get_comments(self):
        '''
        Returns all comments related to this content_item instance,
        regardless of public true/false and ownership of comment
        '''
        return self.comment_model.objects.get_for_contentitem(self)

    def add_comment(self, comment):

        """ Add comment to the content. """
        comment.add_relation_to_instance(self)

    class Meta:
        abstract = True
