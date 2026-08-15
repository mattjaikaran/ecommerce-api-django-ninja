"""Business logic for the loyalty points ledger."""

import logging
from decimal import ROUND_FLOOR, Decimal

from django.db import IntegrityError, transaction

from api.config.constants import LOYALTY_POINTS_PER_DOLLAR
from api.config.error_messages import ERROR_MESSAGES
from api.exceptions import ValidationError
from core.models import Customer
from loyalty.models import LoyaltyAccount, LoyaltyReason, LoyaltyTransaction

logger = logging.getLogger(__name__)


class LoyaltyService:
    @staticmethod
    def get_account(customer: Customer) -> LoyaltyAccount | None:
        """Return the customer's loyalty account without creating one."""
        return LoyaltyAccount.objects.filter(customer=customer).first()

    @staticmethod
    @transaction.atomic
    def get_or_create_account(customer: Customer) -> LoyaltyAccount:
        """Lazily create a loyalty account for the customer."""
        account, _ = LoyaltyAccount.objects.get_or_create(
            customer=customer,
            defaults={"created_by": customer.user},
        )
        return account

    @staticmethod
    @transaction.atomic
    def earn_points(customer: Customer, order, amount: Decimal) -> LoyaltyTransaction:
        """Credit points for an order, idempotent per order.

        Points = floor(amount * LOYALTY_POINTS_PER_DOLLAR). A partial unique
        constraint on (account, order) for earn transactions makes concurrent
        replays race-safe: the losing write is treated as already earned.
        """
        account = LoyaltyService.get_or_create_account(customer)
        points = (Decimal(amount) * LOYALTY_POINTS_PER_DOLLAR).to_integral_value(
            rounding=ROUND_FLOOR
        )
        try:
            with transaction.atomic():
                txn = LoyaltyTransaction.objects.create(
                    account=account,
                    amount=points,
                    order=order,
                    reason=LoyaltyReason.EARN,
                    reference=f"order:{order.id}",
                    created_by=customer.user,
                )
                account.balance += points
                account.lifetime_points += points
                account.updated_by = customer.user
                account.save(
                    update_fields=[
                        "balance",
                        "lifetime_points",
                        "updated_by",
                        "updated_at",
                    ]
                )
        except IntegrityError:
            # Another task already credited this order; the savepoint rolled
            # back this attempt. Return the existing earn transaction.
            logger.info(
                "loyalty points already earned for order",
                extra={"order_id": order.id, "customer_id": customer.id},
            )
            return LoyaltyTransaction.objects.get(
                account=account, order=order, reason=LoyaltyReason.EARN
            )
        return txn

    @staticmethod
    @transaction.atomic
    def redeem_points(
        customer: Customer, points: Decimal, order=None
    ) -> LoyaltyTransaction:
        """Debit points from the customer's balance and record a redeem entry."""
        points = Decimal(points)
        account = LoyaltyService.get_account(customer)
        if account is None or account.balance < points:
            raise ValidationError(ERROR_MESSAGES["insufficient_loyalty_points"])
        reference = f"order:{order.id}" if order else ""
        txn = LoyaltyTransaction.objects.create(
            account=account,
            amount=-points,
            order=order,
            reason=LoyaltyReason.REDEEM,
            reference=reference,
            created_by=customer.user,
        )
        account.balance -= points
        account.updated_by = customer.user
        account.save(update_fields=["balance", "updated_by", "updated_at"])
        return txn

    @staticmethod
    def get_balance(customer: Customer) -> Decimal:
        """Return the customer's current balance, or zero without an account."""
        account = LoyaltyService.get_account(customer)
        if account is None:
            return Decimal("0.00")
        return account.balance
