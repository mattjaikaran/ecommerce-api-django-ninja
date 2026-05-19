import uuid

from django.core.validators import MinValueValidator
from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver

from core.models import AbstractBaseModel, Address, Customer, CustomerGroup

from .choices import OrderStatus, PaymentMethod, PaymentStatus, ShippingMethod


class Order(AbstractBaseModel):
    """Model representing an order."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    order_number = models.CharField(max_length=32, unique=True)
    customer = models.ForeignKey(
        Customer, on_delete=models.PROTECT, related_name="orders"
    )
    customer_group = models.ForeignKey(
        CustomerGroup,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="orders",
    )
    status = models.CharField(
        max_length=50, choices=OrderStatus.choices, default=OrderStatus.DRAFT
    )
    currency = models.CharField(max_length=3, default="USD")
    subtotal = models.DecimalField(
        max_digits=10, decimal_places=2, default=0.00, validators=[MinValueValidator(0)]
    )
    shipping_amount = models.DecimalField(
        max_digits=10, decimal_places=2, default=0.00, validators=[MinValueValidator(0)]
    )
    shipping_method = models.CharField(
        max_length=50, choices=ShippingMethod.choices, default=ShippingMethod.STANDARD
    )
    shipping_tax_amount = models.DecimalField(
        max_digits=10, decimal_places=2, default=0.00, validators=[MinValueValidator(0)]
    )
    discount_amount = models.DecimalField(
        max_digits=10, decimal_places=2, default=0.00, validators=[MinValueValidator(0)]
    )
    tax_amount = models.DecimalField(
        max_digits=10, decimal_places=2, default=0.00, validators=[MinValueValidator(0)]
    )
    total = models.DecimalField(
        max_digits=10, decimal_places=2, default=0.00, validators=[MinValueValidator(0)]
    )
    payment_status = models.CharField(
        max_length=50, choices=PaymentStatus.choices, default=PaymentStatus.PENDING
    )
    payment_method = models.CharField(
        max_length=50, choices=PaymentMethod.choices, default=PaymentMethod.CREDIT_CARD
    )
    payment_gateway = models.CharField(max_length=50, blank=True, null=True)
    payment_gateway_id = models.CharField(max_length=255, blank=True, null=True)
    payment_gateway_response = models.JSONField(blank=True, null=True)
    billing_address = models.ForeignKey(
        Address, on_delete=models.PROTECT, related_name="billing_orders"
    )
    shipping_address = models.ForeignKey(
        Address, on_delete=models.PROTECT, related_name="shipping_orders"
    )
    email = models.EmailField()
    phone = models.CharField(max_length=50, blank=True, null=True)
    customer_note = models.TextField(blank=True, null=True)
    staff_notes = models.TextField(blank=True, null=True)
    ip_address = models.GenericIPAddressField(blank=True, null=True)
    user_agent = models.TextField(blank=True, null=True)
    meta_data = models.JSONField(default=dict, blank=True)

    def __str__(self):
        return f"Order {self.order_number}"

    class Meta:
        verbose_name = "Order"
        verbose_name_plural = "Orders"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["order_number"]),
            models.Index(fields=["status"]),
            models.Index(fields=["payment_status"]),
            models.Index(fields=["created_at"]),
        ]


@receiver(post_save, sender=Order)
def order_post_save(sender, instance, created, **kwargs):
    try:
        from outbound_webhooks.signals import fire_webhook_event

        payload = {
            "id": str(instance.id),
            "status": instance.status,
            "total": str(instance.total),
        }
        event_type = "order.created" if created else "order.updated"
        fire_webhook_event(event_type, payload)
    except Exception:
        pass
