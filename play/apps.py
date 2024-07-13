from django.apps import AppConfig
from django.db.models.signals import post_save


class PlayConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'play'

    def ready(self):
        from . import signals
        from . import models
        post_save.connect(signals.GherkinRuleListener.handle_post_save, sender=models.GherkinRule)
