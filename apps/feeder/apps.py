from django.apps import AppConfig
from django.db.models.signals import post_save


class FeederConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.feeder'
    label = 'feeder'

    def ready(self):
        from django.conf import settings
        from .signals import suggest_save_handler

        Suggest = self.get_model('Suggest')

        # Suggest
        post_save.connect(suggest_save_handler, sender=Suggest,
                          dispatch_uid='suggest_save_signal')
