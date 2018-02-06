from django.core.exceptions import ImproperlyConfigured
from django.apps import apps


# class SwappableMixin(object):
#
#     def get_active_model(self):
#
#         if self._meta.swappable:
#
#             swap_model_string = getattr(settings, self._meta.swappable)
#             try:
#                 return django_apps.get_model(
#                     swap_model_string, require_ready=False)
#             except ValueError:
#                 raise ImproperlyConfigured(
#                     "settings.%s must be of the form "
#                     "'app_label.model_name'" % self._meta.swappable)
#             except LookupError:
#                 raise ImproperlyConfigured(
#                     "settings.%s refers to model '%s' that has not been "
#                     "installed" % (self._meta.swappable, swap_model_string)
#                 )

class SwappableModelMixin(object):

    """ Allow for swapped models. This is an undocumented feature of
    the meta class for now, that enables user defined overrides for
    models (i.e. contrib.auth.User)"""

    @classmethod
    def real_model(self):

        if not hasattr(self._meta, 'swapped') or \
                not self._meta.swapped:
            return self
        else:
            module, model = self._meta.swapped.split(".")
            return apps.get_model(module, model)

    def get_queryset(self):

        """ Override default get_queryset to allow for swappable models """

        if self.queryset is None:
            if self.model:
                return self.real_model()._default_manager.all()
            else:
                raise ImproperlyConfigured(
                    "%(cls)s is missing a queryset. Define "
                    "%(cls)s.model, %(cls)s.queryset, or override "
                    "%(cls)s.get_queryset()." % {
                        'cls': self.__class__.__name__
                    })
        return self.queryset._clone()
