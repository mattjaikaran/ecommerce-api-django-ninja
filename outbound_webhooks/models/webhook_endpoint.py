import secrets
import uuid

from django.db import models


def _default_secret():
    return secrets.token_hex(32)


class WebhookEndpoint(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    url = models.URLField(max_length=500)
    description = models.TextField(blank=True, null=True)
    secret = models.CharField(max_length=64, default=_default_secret)
    events = models.JSONField(default=list)
    is_active = models.BooleanField(default=True)
    failure_count = models.PositiveIntegerField(default=0)
    last_success_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.url

    class Meta:
        verbose_name = "Webhook Endpoint"
        verbose_name_plural = "Webhook Endpoints"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["is_active"]),
        ]
