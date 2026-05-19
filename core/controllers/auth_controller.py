import logging
import secrets
from datetime import datetime, timedelta

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.mail import send_mail
from django.shortcuts import get_object_or_404
from ninja_extra import api_controller, http_post
from ninja_extra.throttling import throttle

from api.decorators import handle_exceptions, log_api_call
from core.models import OneTimePassword
from core.schemas import PasswordlessLoginRequest, PasswordlessLoginVerify
from core.throttles import LoginRateThrottle

User = get_user_model()

logger = logging.getLogger(__name__)


@api_controller("/auth", tags=["Auth"])
class AuthController:
    @http_post("/passwordless/login/request", response={200: dict})
    @throttle(LoginRateThrottle)
    @handle_exceptions
    @log_api_call()
    def request_passwordless_login(self, payload: PasswordlessLoginRequest):
        """Request passwordless login magic link."""
        email = payload.email.lower()
        user_exists = User.objects.filter(email=email).exists()

        if user_exists:
            user = User.objects.get(email=email)
            token = secrets.token_urlsafe(32)
            expires_at = datetime.now() + timedelta(minutes=15)

            OneTimePassword.objects.create(
                user=user, token=token, expires_at=expires_at
            )

            magic_link = f"{settings.FRONTEND_URL}/auth/verify?token={token}"
            send_mail(
                subject="Your Magic Link",
                message=f"Click to login: {magic_link}",
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[email],
                fail_silently=False,
            )

        # Always return success for security (prevent email enumeration)
        return 200, {"detail": "If registered, you'll receive a magic link"}

    @http_post("/passwordless/login/verify", response={200: dict})
    @handle_exceptions
    @log_api_call()
    def verify_passwordless_login(self, payload: PasswordlessLoginVerify):
        """Verify passwordless login token and return JWT tokens."""
        otp = get_object_or_404(
            OneTimePassword.objects.select_related("user"),
            token=payload.token,
            is_used=False,
            expires_at__gte=datetime.now(),
        )

        otp.is_used = True
        otp.save()

        # Generate JWT tokens
        from ninja_jwt.tokens import RefreshToken

        refresh = RefreshToken.for_user(otp.user)
        return 200, {"access": str(refresh.access_token), "refresh": str(refresh)}
