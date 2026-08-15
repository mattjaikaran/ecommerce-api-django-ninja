from django.db import models


class OrderStatus(models.TextChoices):
    DRAFT = "draft", "Draft"
    PENDING = "pending", "Pending"
    PAID = "paid", "Paid"
    PROCESSING = "processing", "Processing"
    SHIPPED = "shipped", "Shipped"
    PARTIALLY_SHIPPED = "partially_shipped", "Partially Shipped"
    DELIVERED = "delivered", "Delivered"
    COMPLETED = "completed", "Completed"
    CANCELLED = "cancelled", "Cancelled"
    REFUNDED = "refunded", "Refunded"
    PARTIALLY_REFUNDED = "partially_refunded", "Partially Refunded"
    FAILED = "failed", "Failed"
    EXPIRED = "expired", "Expired"


# Allowed order status transitions, keyed by current status. The state
# machine is enforced in OrderService.transition_order; staff may force a
# transition with force=True, which bypasses this map but still records
# history.
ORDER_STATUS_TRANSITIONS: dict[str, set[str]] = {
    OrderStatus.DRAFT: {OrderStatus.PENDING},
    OrderStatus.PENDING: {
        OrderStatus.PAID,
        OrderStatus.SHIPPED,
        OrderStatus.PARTIALLY_SHIPPED,
        OrderStatus.CANCELLED,
        OrderStatus.EXPIRED,
        OrderStatus.FAILED,
    },
    OrderStatus.PAID: {
        OrderStatus.PROCESSING,
        OrderStatus.REFUNDED,
        OrderStatus.PARTIALLY_REFUNDED,
    },
    OrderStatus.PROCESSING: {
        OrderStatus.SHIPPED,
        OrderStatus.PARTIALLY_SHIPPED,
        OrderStatus.CANCELLED,
    },
    OrderStatus.PARTIALLY_SHIPPED: {
        OrderStatus.SHIPPED,
        OrderStatus.DELIVERED,
        OrderStatus.PENDING,
        OrderStatus.CANCELLED,
    },
    OrderStatus.SHIPPED: {
        OrderStatus.DELIVERED,
        OrderStatus.PARTIALLY_SHIPPED,
        OrderStatus.PENDING,
        OrderStatus.REFUNDED,
        OrderStatus.PARTIALLY_REFUNDED,
    },
    OrderStatus.DELIVERED: {
        OrderStatus.COMPLETED,
        OrderStatus.REFUNDED,
        OrderStatus.PARTIALLY_REFUNDED,
    },
    OrderStatus.COMPLETED: {
        OrderStatus.REFUNDED,
        OrderStatus.PARTIALLY_REFUNDED,
    },
    # Terminal states
    OrderStatus.CANCELLED: set(),
    OrderStatus.REFUNDED: set(),
    OrderStatus.PARTIALLY_REFUNDED: set(),
    OrderStatus.FAILED: set(),
    OrderStatus.EXPIRED: set(),
}


class PaymentStatus(models.TextChoices):
    PENDING = "pending", "Pending"
    AUTHORIZED = "authorized", "Authorized"
    PAID = "paid", "Paid"
    PARTIALLY_PAID = "partially_paid", "Partially Paid"
    REFUNDED = "refunded", "Refunded"
    PARTIALLY_REFUNDED = "partially_refunded", "Partially Refunded"
    FAILED = "failed", "Failed"
    EXPIRED = "expired", "Expired"
    CANCELLED = "cancelled", "Cancelled"


class PaymentMethod(models.TextChoices):
    CREDIT_CARD = "credit_card", "Credit Card"
    DEBIT_CARD = "debit_card", "Debit Card"
    PAYPAL = "paypal", "PayPal"
    STRIPE = "stripe", "Stripe"
    BANK_TRANSFER = "bank_transfer", "Bank Transfer"
    CASH_ON_DELIVERY = "cash_on_delivery", "Cash on Delivery"
    CRYPTO = "crypto", "Cryptocurrency"


class ShippingMethod(models.TextChoices):
    STANDARD = "standard", "Standard Shipping"
    EXPRESS = "express", "Express Shipping"
    OVERNIGHT = "overnight", "Overnight Shipping"
    FREE = "free", "Free Shipping"
    PICKUP = "pickup", "Local Pickup"
    DIGITAL = "digital", "Digital Delivery"


class FulfillmentStatus(models.TextChoices):
    PENDING = "pending", "Pending"
    PROCESSING = "processing", "Processing"
    SHIPPED = "shipped", "Shipped"
    DELIVERED = "delivered", "Delivered"
    COMPLETED = "completed", "Completed"
    CANCELLED = "cancelled", "Cancelled"
    FAILED = "failed", "Failed"


class RefundStatus(models.TextChoices):
    PENDING = "pending", "Pending"
    PROCESSING = "processing", "Processing"
    COMPLETED = "completed", "Completed"
    FAILED = "failed", "Failed"
    CANCELLED = "cancelled", "Cancelled"


class TaxType(models.TextChoices):
    SALES = "sales", "Sales Tax"
    VAT = "vat", "Value Added Tax"
    GST = "gst", "Goods and Services Tax"
    HST = "hst", "Harmonized Sales Tax"
    PST = "pst", "Provincial Sales Tax"
    CUSTOM = "custom", "Custom Tax"
