from django.apps import AppConfig


class GroupPoliceConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'group_police'

    def ready(self):
        import group_police.signals
