"""Core application constants.

This module contains all the constants used across the application
to ensure consistency and maintainability.
"""

# API Configuration
API_VERSION = "v1"
API_PREFIX = f"/api/{API_VERSION}"

# Pagination Settings
DEFAULT_PAGE_SIZE = 20
MAX_PAGE_SIZE = 100

# Cache Configuration
CACHE_KEY_PREFIX = "ecommerce_api"
CACHE_TIMEOUT_SHORT = 300  # 5 minutes
CACHE_TIMEOUT_MEDIUM = 1800  # 30 minutes
CACHE_TIMEOUT_LONG = 3600  # 1 hour
CACHE_TIMEOUT_DAY = 86400  # 24 hours

# Redis Key Patterns
REDIS_KEYS = {
    "user_sessions": f"{CACHE_KEY_PREFIX}:user_sessions",
    "product_cache": f"{CACHE_KEY_PREFIX}:products",
    "cart_cache": f"{CACHE_KEY_PREFIX}:carts",
    "order_cache": f"{CACHE_KEY_PREFIX}:orders",
    "inventory_cache": f"{CACHE_KEY_PREFIX}:inventory",
    "price_cache": f"{CACHE_KEY_PREFIX}:prices",
    "customer_cache": f"{CACHE_KEY_PREFIX}:customers",
}

# File Upload Settings
MAX_UPLOAD_SIZE = 10 * 1024 * 1024  # 10MB
ALLOWED_IMAGE_EXTENSIONS = [".jpg", ".jpeg", ".png", ".webp", ".gif", ".svg"]
ALLOWED_DOCUMENT_EXTENSIONS = [".pdf", ".doc", ".docx", ".txt", ".csv", ".xlsx"]
ALLOWED_VIDEO_EXTENSIONS = [".mp4", ".avi", ".mov", ".wmv", ".webm"]

# Email Template Paths
EMAIL_TEMPLATES = {
    "welcome": "emails/welcome.html",
    "order_confirmation": "emails/order_confirmation.html",
    "order_shipped": "emails/order_shipped.html",
    "order_delivered": "emails/order_delivered.html",
    "password_reset": "emails/password_reset.html",
    "payment_success": "emails/payment_success.html",
    "payment_failed": "emails/payment_failed.html",
    "shipping_notification": "emails/shipping_notification.html",
    "inventory_low": "emails/inventory_low.html",
    "newsletter": "emails/newsletter.html",
}

# Business Logic Constants
ORDER_STATUS_CHOICES = [
    ("pending", "Pending"),
    ("confirmed", "Confirmed"),
    ("processing", "Processing"),
    ("shipped", "Shipped"),
    ("delivered", "Delivered"),
    ("cancelled", "Cancelled"),
    ("refunded", "Refunded"),
    ("returned", "Returned"),
]

PAYMENT_STATUS_CHOICES = [
    ("pending", "Pending"),
    ("authorized", "Authorized"),
    ("captured", "Captured"),
    ("partial", "Partial"),
    ("failed", "Failed"),
    ("cancelled", "Cancelled"),
    ("refunded", "Refunded"),
    ("disputed", "Disputed"),
]

FULFILLMENT_STATUS_CHOICES = [
    ("pending", "Pending"),
    ("processing", "Processing"),
    ("packed", "Packed"),
    ("shipped", "Shipped"),
    ("delivered", "Delivered"),
    ("returned", "Returned"),
    ("exception", "Exception"),
]

# Loyalty Configuration
LOYALTY_POINTS_PER_DOLLAR = 10

# Currency Settings
DEFAULT_CURRENCY = "USD"
SUPPORTED_CURRENCIES = ["USD", "EUR", "GBP", "CAD", "AUD", "JPY", "CHF", "CNY"]

# Tax Configuration
DEFAULT_TAX_RATE = 0.08  # 8%
TAX_EXEMPT_STATES = ["OR", "MT", "NH", "DE", "AK"]
VAT_COUNTRIES = ["GB", "DE", "FR", "IT", "ES", "NL", "BE", "AT", "PT", "IE"]

# Shipping Configuration
FREE_SHIPPING_THRESHOLD = 50.00
DEFAULT_SHIPPING_COST = 9.99
EXPRESS_SHIPPING_COST = 19.99
OVERNIGHT_SHIPPING_COST = 29.99
INTERNATIONAL_SHIPPING_COST = 39.99

# Product Configuration
PRODUCT_SLUG_MAX_LENGTH = 255
PRODUCT_NAME_MAX_LENGTH = 255
PRODUCT_DESCRIPTION_MAX_LENGTH = 2000
PRODUCT_SKU_MAX_LENGTH = 50

# Inventory Thresholds
LOW_STOCK_THRESHOLD = 10
OUT_OF_STOCK_THRESHOLD = 0
REORDER_THRESHOLD = 5

# User Account Settings
USERNAME_MAX_LENGTH = 150
PHONE_NUMBER_MAX_LENGTH = 20
PASSWORD_MIN_LENGTH = 8

# Security Settings
SESSION_TIMEOUT = 1800  # 30 minutes
MAX_LOGIN_ATTEMPTS = 5
LOCKOUT_DURATION = 900  # 15 minutes
OTP_EXPIRY_MINUTES = 10
JWT_EXPIRY_HOURS = 24

# External Service Timeouts
STRIPE_WEBHOOK_TOLERANCE = 300  # 5 minutes
SENDGRID_TIMEOUT = 30  # seconds
AWS_S3_TIMEOUT = 60  # seconds
PAYMENT_GATEWAY_TIMEOUT = 30  # seconds

# Logging Configuration
LOG_LEVELS = {
    "DEBUG": 10,
    "INFO": 20,
    "WARNING": 30,
    "ERROR": 40,
    "CRITICAL": 50,
}

# Health Check Services
HEALTH_CHECK_SERVICES = [
    "database",
    "redis",
    "s3",
    "stripe",
    "email",
    "celery",
]

# Rate Limiting
RATE_LIMIT_PER_MINUTE = 60
RATE_LIMIT_PER_HOUR = 1000
RATE_LIMIT_PER_DAY = 10000
RATE_LIMIT_BURST = 10

# Idempotency Configuration
IDEMPOTENCY_KEY_TTL_HOURS = 24  # idempotency keys expire after 24 hours

# Search Configuration
SEARCH_RESULTS_PER_PAGE = 20
MAX_SEARCH_RESULTS = 1000
SEARCH_TIMEOUT = 5  # seconds
MIN_SEARCH_QUERY_LENGTH = 2

# Analytics & Tracking
ANALYTICS_BATCH_SIZE = 100
ANALYTICS_FLUSH_INTERVAL = 300  # 5 minutes
CONVERSION_TRACKING_COOKIE_DAYS = 30

# Feature Flags
FEATURES = {
    "ENABLE_RECOMMENDATIONS": True,
    "ENABLE_WISHLIST": True,
    "ENABLE_REVIEWS": True,
    "ENABLE_LOYALTY_PROGRAM": False,
    "ENABLE_MULTI_CURRENCY": True,
    "ENABLE_INVENTORY_TRACKING": True,
}

# Date/Time Formats
DATE_FORMAT = "%Y-%m-%d"
DATETIME_FORMAT = "%Y-%m-%d %H:%M:%S"
TIME_FORMAT = "%H:%M:%S"
