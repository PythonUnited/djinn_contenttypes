from django.apps import AppConfig
from django.db.models import signals


class DjinnContenttypesAppConfig(AppConfig):
    name = 'djinn_contenttypes'

    def ready(self):

        # here to initiate the signal processors after django models have been
        # initialized
        # from pgeditorial import signal_processors

        from djinn_contenttypes.management import create_permissions
        signals.post_migrate.connect(create_permissions, sender=self)
