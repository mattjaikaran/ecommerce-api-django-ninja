from debug_toolbar.toolbar import debug_toolbar_urls
from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path
from ninja import Redoc
from ninja_extra import NinjaExtraAPI
from ninja_jwt.controller import NinjaJWTDefaultController

from coupons.controllers import CouponController
from analytics.controllers import (
    CustomerAnalyticsController,
    PerformanceMetricController,
    ProductAnalyticsController,
    SalesReportController,
)
from cart.controllers import CartController, CartItemController
from core.controllers import AuthController, CustomerController, UserController
from orders.controllers import DiscountController, OrderController
from payments.controllers import PaymentController
from payments.webhooks import stripe_webhook
from products.controllers import (
    AttributeController,
    BundleController,
    CategoryController,
    CollectionController,
    ProductController,
    ProductOptionController,
    ReviewController,
    TagController,
)

# Health check imports
from .healthcheck import (
    health_check_all,
    health_check_service,
    health_check_simple,
    liveness_check,
    monitoring_info,
    readiness_check,
)

# admin site settings
admin.site.site_header = "E-Commerce Admin"
admin.site.site_title = "E-Commerce Panel"
admin.site.index_title = "Welcome to E-Commerce Panel"
admin.site.site_url = "/api/docs"

api = NinjaExtraAPI(
    version="1.0.0",
    title="E-Commerce API",
    description="API documentation for the E-Commerce API",
    urls_namespace="api_v1",
    docs=Redoc(),
    auth=None,
    csrf=False,
)

# Register controllers
api.register_controllers(
    NinjaJWTDefaultController,
    UserController,
    AuthController,
    CustomerController,
    # Register specific product-related controllers first
    CategoryController,
    CollectionController,
    TagController,
    ProductOptionController,
    AttributeController,
    BundleController,
    ReviewController,
    # Register the general product controller last
    ProductController,
    CartController,
    CartItemController,
    OrderController,
    DiscountController,
    PaymentController,
    CouponController,
    SalesReportController,
    PerformanceMetricController,
    ProductAnalyticsController,
    CustomerAnalyticsController,
)

# Health check patterns
health_patterns = [
    path("health/", health_check_simple, name="health-simple"),
    path("health/all/", health_check_all, name="health-all"),
    path("health/<str:service_name>/", health_check_service, name="health-service"),
    path("readiness/", readiness_check, name="readiness"),
    path("liveness/", liveness_check, name="liveness"),
    path("monitoring/", monitoring_info, name="monitoring"),
]

urlpatterns = [
    # Admin
    path("admin/", admin.site.urls),
    # API
    path("api/", api.urls),
    # Stripe webhook (raw body required — outside of NinjaExtraAPI)
    path("webhooks/stripe/", stripe_webhook, name="stripe-webhook"),
    # Health checks
    path("", include(health_patterns)),
    # Debug toolbar (development only)
    *debug_toolbar_urls(),
]

if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
