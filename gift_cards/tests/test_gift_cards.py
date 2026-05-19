from decimal import Decimal
from unittest.mock import MagicMock

import pytest
from django.http import Http404
from django.utils import timezone

from gift_cards.models import GiftCard, GiftCardTransaction
from gift_cards.models.gift_card_transaction import TransactionType
from gift_cards.services import GiftCardService
from gift_cards.tests.factories import GiftCardFactory


@pytest.mark.django_db
class TestGiftCardGeneration:
    def test_generate_code_format(self):
        code = GiftCardService.generate_code()
        parts = code.split("-")
        assert len(parts) == 4
        for part in parts:
            assert len(part) == 4
            assert part.isupper() or part.isdigit() or part.isalnum()

    def test_generated_codes_are_unique(self):
        codes = {GiftCardService.generate_code() for _ in range(20)}
        assert len(codes) == 20

    def test_create_gift_card(self):
        gc = GiftCardService.create_gift_card(Decimal("50.00"))
        assert gc.initial_balance == Decimal("50.00")
        assert gc.current_balance == Decimal("50.00")
        assert gc.is_active is True
        assert gc.code


@pytest.mark.django_db
class TestGiftCardRedemption:
    def test_redeem_deducts_balance(self):
        gc = GiftCardFactory(initial_balance=Decimal("100.00"), current_balance=Decimal("100.00"))
        txn = GiftCardService.redeem(gc, Decimal("30.00"))
        gc.refresh_from_db()
        assert gc.current_balance == Decimal("70.00")
        assert txn.transaction_type == TransactionType.REDEEMED
        assert txn.amount == Decimal("-30.00")

    def test_redeem_insufficient_balance_raises(self):
        gc = GiftCardFactory(initial_balance=Decimal("10.00"), current_balance=Decimal("10.00"))
        with pytest.raises(ValueError, match="Insufficient"):
            GiftCardService.redeem(gc, Decimal("50.00"))

    def test_get_balance(self):
        gc = GiftCardFactory(current_balance=Decimal("75.00"))
        balance = GiftCardService.get_balance(gc.code)
        assert balance == Decimal("75.00")

    def test_get_balance_inactive_card_raises(self):
        gc = GiftCardFactory(is_active=False)
        with pytest.raises(Http404):
            GiftCardService.get_balance(gc.code)


@pytest.mark.django_db
class TestGiftCardCartApplication:
    def test_apply_expired_card_raises(self):
        past = timezone.now().replace(year=2020)
        gc = GiftCardFactory(
            current_balance=Decimal("50.00"),
            expires_at=past,
        )
        cart = MagicMock()
        cart.total_price = Decimal("100.00")

        from gift_cards.services.gift_card_service import GiftCardService as GCS

        with pytest.raises(ValueError, match="expired"):
            GCS.apply_to_cart(cart, gc.code)

    def test_apply_zero_balance_card_raises(self):
        gc = GiftCardFactory(current_balance=Decimal("0.00"))
        cart = MagicMock()
        cart.total_price = Decimal("100.00")

        with pytest.raises(ValueError, match="no remaining balance"):
            GiftCardService.apply_to_cart(cart, gc.code)
