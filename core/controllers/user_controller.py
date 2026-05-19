"""User management controller with modern decorator-based approach."""

import logging
from uuid import UUID

from django.contrib.auth import authenticate, get_user_model
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.shortcuts import get_object_or_404
from ninja_extra import api_controller, http_delete, http_get, http_post, http_put
from ninja_extra.throttling import throttle
from ninja_jwt.tokens import RefreshToken

from api.decorators import (
    create_endpoint,
    delete_endpoint,
    detail_endpoint,
    list_endpoint,
    search_and_filter,
    update_endpoint,
)
from api.exceptions import AuthenticationError as APIAuthenticationError
from core.schemas import (
    UserLoginSchema,
    UserSchema,
    UserSignupSchema,
    UserUpdateSchema,
)
from core.throttles import LoginRateThrottle, RegisterRateThrottle

logger = logging.getLogger(__name__)

User = get_user_model()


@api_controller("/users", tags=["Users"])
class UserController:
    """User management controller with comprehensive decorators."""

    @http_post("/signup", response={201: UserSchema, 400: dict, 401: dict, 403: dict})
    @throttle(RegisterRateThrottle)
    @create_endpoint(require_auth=False)
    def signup(self, request, data: UserSignupSchema):
        """Create a new user account."""
        # Check if username exists
        if User.objects.filter(username=data.username).exists():
            validation_error = ValidationError(
                "A user with this username already exists."
            )
            raise validation_error

        # Check if email exists
        if User.objects.filter(email=data.email).exists():
            validation_error = ValidationError("A user with this email already exists.")
            raise validation_error

        # Validate password
        validate_password(data.password)

        # Create user
        user = User.objects.create_user(
            username=data.username,
            email=data.email,
            password=data.password,
            first_name=data.first_name,
            last_name=data.last_name,
            is_staff=False,
            is_superuser=False,
        )
        return 201, UserSchema.from_orm(user)

    @http_post("/login", response={200: dict, 400: dict, 401: dict, 403: dict})
    @throttle(LoginRateThrottle)
    @create_endpoint(require_auth=False)
    def login(self, request, data: UserLoginSchema):
        """Authenticate user and return tokens."""
        user = authenticate(username=data.username, password=data.password)
        if not user:
            raise APIAuthenticationError("Invalid credentials")

        # Generate token
        refresh = RefreshToken.for_user(user)
        return 200, {
            "token": str(refresh.access_token),
            "refresh": str(refresh),
            "user": UserSchema.from_orm(user).dict(),
        }

    @http_get("", response={200: list[UserSchema], 401: dict, 403: dict})
    @list_endpoint(
        require_admin=True,
        search_fields=["username", "email", "first_name", "last_name"],
        filter_fields={
            "is_staff": "boolean",
            "is_superuser": "boolean",
            "is_active": "boolean",
        },
        ordering_fields=["username", "email", "date_joined", "first_name", "last_name"],
    )
    @search_and_filter(
        search_fields=["username", "email", "first_name", "last_name"],
        filter_fields={
            "is_staff": "boolean",
            "is_superuser": "boolean",
        },
        ordering_fields=["username", "email", "date_joined"],
    )
    def list_users(self, request):
        """Get all users with advanced filtering and search."""
        return 200, User.objects.all()

    @http_get("/me", response={200: UserSchema, 401: dict})
    @detail_endpoint()
    def get_current_user(self, request):
        """Get the current authenticated user."""
        return 200, UserSchema.from_orm(request.user)

    @http_get("/{user_id}", response={200: UserSchema, 404: dict, 401: dict, 403: dict})
    @detail_endpoint(
        require_auth=True,
        select_related=["groups", "user_permissions"],
    )
    def get_user(self, request, user_id: UUID):
        """Get a specific user by ID. Users can access their own profile; admins can access any."""
        if not request.user.is_staff and str(request.user.id) != str(user_id):
            from api.exceptions import APIPermissionError
            raise APIPermissionError("Permission denied")
        user = get_object_or_404(User, id=user_id)
        return 200, UserSchema.from_orm(user)

    @http_put("/{user_id}", response={200: UserSchema, 400: dict, 404: dict, 401: dict, 403: dict, 409: dict})
    @update_endpoint(require_admin=True)
    def update_user(self, request, user_id: UUID, payload: UserUpdateSchema):
        """Update a user's information."""
        user = get_object_or_404(User, id=user_id)

        for attr, value in payload.dict(exclude_unset=True).items():
            setattr(user, attr, value)

        user.save()
        return 200, UserSchema.from_orm(user)

    @http_delete("/{user_id}", response={204: None, 404: dict, 401: dict, 403: dict})
    @delete_endpoint(require_admin=True)
    def delete_user(self, request, user_id: UUID):
        """Delete a user account."""
        user = get_object_or_404(User, id=user_id)
        user.delete()
        return 204, None

    @http_get("/search", response={200: list[UserSchema], 401: dict, 403: dict})
    @list_endpoint(
        require_auth=True,
        cache_timeout=300,
        search_fields=["username", "email", "first_name", "last_name"],
        filter_fields={
            "is_staff": "boolean",
            "is_active": "boolean",
        },
        ordering_fields=["username", "email", "date_joined"],
    )
    @search_and_filter(
        search_fields=["username", "email", "first_name", "last_name"],
        filter_fields={
            "is_staff": "boolean",
            "is_active": "boolean",
        },
        ordering_fields=["username", "email", "date_joined"],
    )
    def search_users(self, request):
        """Advanced user search with filtering."""
        return 200, User.objects.filter(is_active=True)
