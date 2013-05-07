import logging
from pgcontent.models.simplerelation import SimpleRelation


LOG = logging.getLogger("pgcontent")


class RelatableMixin:

    """ Mixin class that enables relations."""

    def get_related(self, relation_type=None):

        """ Return all related content. This is a costly operation, so
        use it wisely..."""

        if relation_type:
            relations = self.get_relations(relation_type_list=[relation_type])
        else:
            relations = self.get_relations()

        related = []

        for rel in relations:
            try:
                related.append(rel.get_tgt())
            except:
                LOG.warn("Cleaning up broken relation %s" % rel)
                rel.delete()

        return related

    def get_relations(self, relation_type_list=[], target_type=None,
                      inverse=False):

        """
        Get all relations for the given object. If relation_type
        is set, return only these relations. If inverse is true,
        return inverse relations.

        Returns a Filter result.
        """

        if not inverse:
            _filter = {'src_content_type': self.ct_class,
              'src_object_id': self.id}
        else:
            _filter = {'tgt_content_type': self.ct_class,
                 'tgt_object_id': self.id}

        if len(relation_type_list):
            _filter['relation_type__in'] = relation_type_list

        if target_type:
            _filter['tgt_content_type'] = target_type

        return SimpleRelation.objects.filter(**_filter)

    def add_relation(self, relation_type, target, unique=True):

        """ Add relation with given type with target as receiving end.
        If unique is true, don't add if it's already there..."""

        if unique and self.has_relation(relation_type, target):
            return None

        return SimpleRelation.objects.create(src_content_type=self.ct_class,
                                             src_object_id=self.id,
                                             relation_type=relation_type,
                                             tgt_content_type=target.ct_class,
                                             tgt_object_id=target.id)

    def has_relation(self, relation_type, target):

        """ Add relation with given type with target as receiving end."""

        return SimpleRelation.objects.filter(src_content_type=self.ct_class,
                                             src_object_id=self.id,
                                             relation_type=relation_type,
                                             tgt_content_type=target.ct_class,
                                             tgt_object_id=target.id).exists()

    def rm_relation(self, relation_type, target):

        """ Remove relation with given type with target as receiving
        end."""

        SimpleRelation.objects.filter(src_content_type=self.ct_class,
                                   src_object_id=self.id,
                                   relation_type=relation_type,
                                   tgt_content_type=target.ct_class,
                                   tgt_object_id=target.id).delete()

    def rm_all_relations(self, inverse=True):

        """ Remove all relations. If inverse is true=ish, also remove
        relations where self is the target. """

        self.get_relations().delete()
        if inverse:
            self.get_relations(inverse=True).delete()

