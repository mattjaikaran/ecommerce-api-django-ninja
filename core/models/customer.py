"""Customer and customer group model definitions."""

from django.db import models

from .abstract_base import AbstractBaseModel
from .user import User


class Customer(AbstractBaseModel):
    """Model for storing customer-specific information."""

    user = models.OneToOneField(User, on_delete=models.CASCADE)
    phone = models.CharField(max_length=255)
    is_default = models.BooleanField(default=False)
    stripe_customer_id = models.CharField(max_length=255, blank=True, default="")

    def __str__(self):
        return f"{self.user.username} - {self.phone}"

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Customer"
        verbose_name_plural = "Customers"
        indexes = [
            models.Index(fields=["user"]),
            models.Index(fields=["phone"]),
            models.Index(fields=["is_default"]),
        ]


class CustomerGroup(AbstractBaseModel):
    """Model for organizing customers into groups."""

    name = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    customers = models.ManyToManyField(Customer, related_name="customer_groups")

    def __str__(self):
        return self.name

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Customer Group"
        verbose_name_plural = "Customer Groups"
        indexes = [
            models.Index(fields=["name"]),
        ]
