import logging
from django.db import models


LOG = logging.getLogger("djinn_contenttypes")


class RelatableMixin(object):

    """ Mixin class that enables relations."""

    @property
    def relation_model(self):

        """ Dynamically fetch model, so as to remove module dependency """

        return models.get_model("pgcontent", "SimpleRelation")

    def get_related(self, relation_type=None, inverse=False):

        """ Return all related content. This is a costly operation, so
        use it wisely..."""

        if relation_type:
            relations = self.get_relations(relation_type_list=[relation_type],
                                           inverse=inverse)
        else:
            relations = self.get_relations()

        related = []

        for rel in relations:
            try:
                if inverse:
                    relation_source = rel.get_src()
                    relation_source._meta  # force a check
                    related.append(relation_source)
                else:
                    relation_target = rel.get_tgt()
                    relation_target._meta
                    related.append(relation_target)
            except:
                LOG.warn("Cleaning up broken relation %s", rel)
                rel.delete()

        return related

    def get_relations(self, relation_type_list=None, target_type=None,
                      inverse=False):

        """
        Get all relations for the given object. If relation_type
        is set, return only these relations. If inverse is true,
        return inverse relations.

        Returns a Filter result.
        """

        if not relation_type_list:
            relation_type_list = []

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

        return self.relation_model.objects.filter(**_filter)

    def add_relation(self, relation_type, target, unique=True):

        """ Add relation with given type with target as receiving end.
        If unique is true, don't add if it's already there..."""

        if unique and self.has_relation(relation_type, target):
            return None

        return self.relation_model.objects.create(
            src_content_type=self.ct_class,
            src_object_id=self.id,
            relation_type=relation_type,
            tgt_content_type=target.ct_class,
            tgt_object_id=target.id)

    def has_relation(self, relation_type, target=None, inverse=False):

        """Do we have a relation? With target? If inverse is set, check
        that...

        """

        _filter = {'relation_type': relation_type}

        if inverse:
            _filter.update(
                {'tgt_content_type': self.ct_class,
                 'tgt_object_id': self.id})
        else:
            _filter.update(
                {'src_content_type': self.ct_class,
                 'src_object_id': self.id})

        if target:
            if inverse:
                _filter.update(
                    {'src_content_type': target.ct_class,
                     'src_object_id': target.id})
            else:
                _filter.update(
                    {'tgt_content_type': target.ct_class,
                     'tgt_object_id': target.id})

        return self.relation_model.objects.filter(**_filter).exists()

    def rm_relation(self, relation_type, target):

        """ Remove relation with given type with target as receiving
        end."""

        self.relation_model.objects.filter(
            src_content_type=self.ct_class,
            src_object_id=self.id,
            relation_type=relation_type,
            tgt_content_type=target.ct_class,
            tgt_object_id=target.id).delete()

    def rm_all_relations(self, inverse=True):

        """ Remove all relations. If inverse is true=ish, also remove
        relations where self is the target. """

    def save_relations(self):

        """ Save all relations set for the current object """

        # if this instance has a '_relation_updater' attribute, then
        # iterate over them, and call the update method
        if hasattr(self, '_relation_updater'):
            for updater in self._relation_updater:
                updater.update()
            # clean up, so another save won't mess up
            delattr(self, '_relation_updater')


class RelatableModel(models.Model, RelatableMixin):

    """ A model with the relatable stuff builtin """

    class Meta:

        """ Make the base model abstract """

        abstract = True

    def save(self):
        """ save the model + the relations """

        super(RelatableModel, self).save()
        self.save_relations()
