import uuid

from django.db import models

from .subscription_plan import SubscriptionPlan


class SubscriptionStatus(models.TextChoices):
    ACTIVE = "active", "Active"
    PAST_DUE = "past_due", "Past Due"
    CANCELED = "canceled", "Canceled"
    TRIALING = "trialing", "Trialing"
    INCOMPLETE = "incomplete", "Incomplete"
    UNPAID = "unpaid", "Unpaid"


class CustomerSubscription(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    customer = models.ForeignKey(
        "core.Customer", on_delete=models.CASCADE, related_name="subscriptions"
    )
    plan = models.ForeignKey(
        SubscriptionPlan, on_delete=models.SET_NULL, null=True, blank=True
    )
    stripe_subscription_id = models.CharField(max_length=200, unique=True)
    stripe_customer_id = models.CharField(max_length=200)
    status = models.CharField(
        max_length=20, choices=SubscriptionStatus.choices, default=SubscriptionStatus.INCOMPLETE
    )
    current_period_start = models.DateTimeField(null=True, blank=True)
    current_period_end = models.DateTimeField(null=True, blank=True)
    cancel_at_period_end = models.BooleanField(default=False)
    canceled_at = models.DateTimeField(null=True, blank=True)
    trial_end = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.customer} - {self.stripe_subscription_id}"

    class Meta:
        verbose_name = "Customer Subscription"
        verbose_name_plural = "Customer Subscriptions"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["customer"]),
            models.Index(fields=["status"]),
            models.Index(fields=["stripe_subscription_id"]),
        ]
