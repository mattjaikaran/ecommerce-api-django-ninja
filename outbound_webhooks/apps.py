from django.apps import AppConfig


class OutboundWebhooksConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "outbound_webhooks"
    verbose_name = "Outbound Webhooks"

    def ready(self):
        import outbound_webhooks.signals  # noqa: F401
