from django.db import models


class LoyaltyReason(models.TextChoices):
    EARN = "earn", "Earn"
    REDEEM = "redeem", "Redeem"
    ADJUST = "adjust", "Adjust"
