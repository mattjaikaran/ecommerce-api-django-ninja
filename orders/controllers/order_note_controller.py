from django.db import transaction
from django.shortcuts import get_object_or_404
from ninja.pagination import paginate
from ninja_extra import (
    api_controller,
    http_delete,
    http_get,
    http_post,
    http_put,
)
from ninja_extra.permissions import IsAuthenticated

from api.decorators import handle_exceptions, log_api_call
from api.exceptions import APIPermissionError as PermissionDeniedError, NotFoundError
from orders.models import (
    Order,
    OrderNote,
)
from orders.schemas import (
    OrderNoteCreateSchema,
    OrderNoteSchema,
)


@api_controller("/orders/{order_id}/notes", tags=["Order Notes"])
class OrderNoteController:
    permission_classes = [IsAuthenticated]

    @http_get("", response={200: list[OrderNoteSchema]})
    @handle_exceptions
    @log_api_call()
    @paginate
    def list_notes(self, request, order_id: str):
        """Get paginated list of notes for an order."""
        order = get_object_or_404(Order, id=order_id)
        notes = OrderNote.objects.select_related("order", "created_by").filter(
            order=order
        )

        # Filter notes based on user role
        if not request.user.is_staff:
            notes = notes.filter(is_customer_visible=True)

        return 200, notes.order_by("-created_at")

    @http_get("/{note_id}", response={200: OrderNoteSchema})
    @handle_exceptions
    @log_api_call()
    def get_note(self, request, order_id: str, note_id: str):
        """Get single note by ID."""
        order = get_object_or_404(Order, id=order_id)
        note = get_object_or_404(
            OrderNote.objects.select_related("order", "created_by"),
            id=note_id,
            order=order,
        )

        # Check visibility for non-staff users
        if not request.user.is_staff and not note.is_customer_visible:
            raise NotFoundError("Note not found")

        return 200, note

    @http_post("", response={201: OrderNoteSchema})
    @handle_exceptions
    @log_api_call()
    @transaction.atomic
    def create_note(self, request, order_id: str, payload: OrderNoteCreateSchema):
        """Create new note for an order."""
        order = get_object_or_404(Order, id=order_id)

        note = OrderNote.objects.create(
            order=order,
            content=payload.content,
            is_customer_visible=payload.is_customer_visible,
            created_by=request.user,
        )
        return 201, note

    @http_put("/{note_id}", response={200: OrderNoteSchema})
    @handle_exceptions
    @log_api_call()
    @transaction.atomic
    def update_note(
        self, request, order_id: str, note_id: str, payload: OrderNoteCreateSchema
    ):
        """Update existing note."""
        order = get_object_or_404(Order, id=order_id)
        note = get_object_or_404(OrderNote, id=note_id, order=order)

        # Only allow staff to update notes or the creator
        if not request.user.is_staff and note.created_by != request.user:
            raise PermissionDeniedError("Not authorized to update this note")

        # Update note fields
        for field, value in payload.model_dump(exclude_unset=True).items():
            setattr(note, field, value)
        note.save()

        return 200, note

    @http_delete("/{note_id}", response={204: None})
    @handle_exceptions
    @log_api_call()
    @transaction.atomic
    def delete_note(self, request, order_id: str, note_id: str):
        """Delete note."""
        order = get_object_or_404(Order, id=order_id)
        note = get_object_or_404(OrderNote, id=note_id, order=order)

        # Only allow staff to delete notes or the creator
        if not request.user.is_staff and note.created_by != request.user:
            raise PermissionDeniedError("Not authorized to delete this note")

        note.delete()
        return 204, None

    @http_get("/customer-visible", response={200: list[OrderNoteSchema]})
    @handle_exceptions
    @log_api_call()
    @paginate
    def list_customer_visible_notes(self, request, order_id: str):
        """Get paginated list of customer-visible notes for an order."""
        order = get_object_or_404(Order, id=order_id)
        notes = (
            OrderNote.objects.select_related("order", "created_by")
            .filter(order=order, is_customer_visible=True)
            .order_by("-created_at")
        )
        return 200, notes

    @http_get("/internal", response={200: list[OrderNoteSchema]})
    @handle_exceptions
    @log_api_call()
    @paginate
    def list_internal_notes(self, request, order_id: str):
        """Get paginated list of internal notes for an order (staff only)."""
        if not request.user.is_staff:
            raise PermissionDeniedError("Staff access required")

        order = get_object_or_404(Order, id=order_id)
        notes = (
            OrderNote.objects.select_related("order", "created_by")
            .filter(order=order, is_customer_visible=False)
            .order_by("-created_at")
        )
        return 200, notes
