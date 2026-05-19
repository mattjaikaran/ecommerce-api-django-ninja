import random
import string
from decimal import Decimal

from django.http import Http404
from django.utils import timezone

from gift_cards.models import CartGiftCard, GiftCard, GiftCardTransaction
from gift_cards.models.gift_card_transaction import TransactionType


class GiftCardService:
    @staticmethod
    def generate_code() -> str:
        chars = string.ascii_uppercase + string.digits
        groups = ["".join(random.choices(chars, k=4)) for _ in range(4)]
        return "-".join(groups)

    @staticmethod
    def create_gift_card(
        amount: Decimal,
        issued_to=None,
        expires_at=None,
        created_by=None,
    ) -> GiftCard:
        code = GiftCardService.generate_code()
        while GiftCard.objects.filter(code=code).exists():
            code = GiftCardService.generate_code()

        return GiftCard.objects.create(
            code=code,
            initial_balance=amount,
            current_balance=amount,
            issued_to=issued_to,
            expires_at=expires_at,
            created_by=created_by,
        )

    @staticmethod
    def get_by_code(code: str) -> GiftCard:
        try:
            return GiftCard.objects.get(code=code.upper(), is_active=True)
        except GiftCard.DoesNotExist:
            raise Http404(f"Gift card '{code}' not found or inactive")

    @staticmethod
    def apply_to_cart(cart, code: str) -> CartGiftCard:
        gift_card = GiftCardService.get_by_code(code)

        if gift_card.current_balance <= 0:
            raise ValueError("Gift card has no remaining balance")

        if gift_card.expires_at and gift_card.expires_at < timezone.now():
            raise ValueError("Gift card has expired")

        if CartGiftCard.objects.filter(cart=cart, gift_card=gift_card).exists():
            raise ValueError("Gift card already applied to this cart")

        amount_applied = min(gift_card.current_balance, cart.total_price)
        return CartGiftCard.objects.create(
            cart=cart,
            gift_card=gift_card,
            amount_applied=amount_applied,
        )

    @staticmethod
    def redeem(gift_card: GiftCard, amount: Decimal, order_id=None) -> GiftCardTransaction:
        if gift_card.current_balance < amount:
            raise ValueError("Insufficient gift card balance")

        gift_card.current_balance -= amount
        gift_card.save(update_fields=["current_balance", "updated_at"])

        return GiftCardTransaction.objects.create(
            gift_card=gift_card,
            amount=-amount,
            transaction_type=TransactionType.REDEEMED,
            order_id=order_id,
        )

    @staticmethod
    def get_balance(code: str) -> Decimal:
        gift_card = GiftCardService.get_by_code(code)
        return gift_card.current_balance
