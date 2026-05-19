from datetime import datetime
from decimal import Decimal
from uuid import UUID

from django.shortcuts import get_object_or_404
from ninja import Schema
from ninja.pagination import paginate
from ninja_extra import api_controller, http_delete, http_get, http_post
from ninja_extra.permissions import IsAuthenticated

from gift_cards.models import CartGiftCard, GiftCard
from gift_cards.services import GiftCardService


class GiftCardSchema(Schema):
    id: UUID
    code: str
    initial_balance: Decimal
    current_balance: Decimal
    is_active: bool
    issued_to_id: UUID | None = None
    expires_at: datetime | None = None
    created_at: datetime


class GiftCardCreateSchema(Schema):
    amount: Decimal
    issued_to_id: UUID | None = None
    expires_at: datetime | None = None


class ApplyGiftCardSchema(Schema):
    code: str
    cart_id: UUID


class BalanceSchema(Schema):
    balance: Decimal


@api_controller("/gift-cards", tags=["Gift Cards"])
class GiftCardController:
    permission_classes = [IsAuthenticated]

    @http_get("", response={200: list[GiftCardSchema]})
    @paginate
    def list_gift_cards(self, request):
        return GiftCard.objects.all()

    @http_post("", response={201: GiftCardSchema})
    def create_gift_card(self, request, payload: GiftCardCreateSchema):
        gift_card = GiftCardService.create_gift_card(
            amount=payload.amount,
            expires_at=payload.expires_at,
            created_by=request.user,
        )
        return 201, gift_card

    @http_get("/{code}/balance", response={200: BalanceSchema})
    def get_balance(self, request, code: str):
        balance = GiftCardService.get_balance(code)
        return 200, BalanceSchema(balance=balance)

    @http_post("/apply", response={201: dict})
    def apply_to_cart(self, request, payload: ApplyGiftCardSchema):
        from cart.models import Cart

        cart = get_object_or_404(Cart, id=payload.cart_id)
        cart_gift_card = GiftCardService.apply_to_cart(cart, payload.code)
        return 201, {
            "message": "Gift card applied",
            "amount_applied": str(cart_gift_card.amount_applied),
        }

    @http_delete("/cart/{cart_id}/remove/{code}", response={204: None})
    def remove_from_cart(self, request, cart_id: UUID, code: str):
        gift_card = get_object_or_404(GiftCard, code=code.upper())
        CartGiftCard.objects.filter(cart_id=cart_id, gift_card=gift_card).delete()
        return 204, None
