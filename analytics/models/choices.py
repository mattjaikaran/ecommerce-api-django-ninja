from django.db import models


class MetricType(models.TextChoices):
    REVENUE = "revenue", "Revenue"
    ORDERS = "orders", "Orders"
    CUSTOMERS = "customers", "Customers"
    AOV = "aov", "Average Order Value"
    CONVERSION_RATE = "conversion_rate", "Conversion Rate"
    CART_ABANDONMENT = "cart_abandonment", "Cart Abandonment Rate"
    REFUND_RATE = "refund_rate", "Refund Rate"


class ReportType(models.TextChoices):
    SALES = "sales", "Sales Report"
    INVENTORY = "inventory", "Inventory Report"
    CUSTOMER = "customer", "Customer Report"
    PRODUCT = "product", "Product Performance Report"


class TimePeriod(models.TextChoices):
    DAILY = "daily", "Daily"
    WEEKLY = "weekly", "Weekly"
    MONTHLY = "monthly", "Monthly"
    QUARTERLY = "quarterly", "Quarterly"
    YEARLY = "yearly", "Yearly"
