from django.apps import AppConfig


class IpifHubConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "ipif_hub"

    def ready(self):
        import ipif_hub.signals.handlers  # noqa: F401
