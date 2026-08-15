"""X-Request-ID correlation: middleware, context var, and logging filter."""

import logging
import uuid
from contextvars import ContextVar

# Allowed characters in a sanitized request id.
_ALLOWED = frozenset(
    "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789_-."
)
_MAX_LENGTH = 100

request_id_var: ContextVar[str] = ContextVar("request_id", default="")


def get_request_id() -> str:
    """Return the current request id from the context var."""
    return request_id_var.get()


def sanitize_request_id(value: str) -> str:
    """Strip and keep only [A-Za-z0-9_.-]; cap at 100 chars; "" if empty."""
    cleaned = "".join(ch for ch in value.strip() if ch in _ALLOWED)
    return cleaned[:_MAX_LENGTH]


class RequestIdMiddleware:
    """Accept, generate, and echo the X-Request-ID header for each request."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        incoming = request.headers.get("X-Request-ID", "")
        request_id = sanitize_request_id(incoming) or uuid.uuid4().hex
        request.request_id = request_id
        token = request_id_var.set(request_id)
        try:
            response = self.get_response(request)
        finally:
            request_id_var.reset(token)
        response["X-Request-ID"] = request_id
        return response


class RequestIdLogFilter(logging.Filter):
    """Attach the current request id to every log record."""

    def filter(self, record):
        record.request_id = request_id_var.get() or "-"
        return True
