from django.db import models


class DiscountType(models.TextChoices):
    PERCENTAGE = "percentage", "Percentage"
    FIXED_AMOUNT = "fixed_amount", "Fixed Amount"
    FREE_SHIPPING = "free_shipping", "Free Shipping"
