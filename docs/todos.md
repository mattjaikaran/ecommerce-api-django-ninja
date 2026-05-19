# TODO

## Apps Structure

- [x] Core App
  - Authentication, Users, Base Models
  - Permissions and Groups
  - Settings and Configuration
  - Customer Models (Customer, CustomerGroup)
  - Address Management
  - Customer Feedback
- [x] Products App
  - Products, Variants, Options
  - Categories and Collections
  - Inventory Management
  - SEO Fields
  - Status (draft, active, archived)
  - Images and Reviews
  - Tags and Attributes
  - Product Bundles
  - Price and Inventory History
- [x] Orders App
  - Orders and Line Items
  - Order Status Management
  - Order History and Notes
  - Fulfillment Tracking
  - **Tax Models and Calculations** (built-in)
  - **Discount Models** (built-in)
  - **Payment Processing** (built-in)
  - **Refund Management** (built-in)
- [x] Cart App
  - Shopping Cart
  - Cart Items
  - Cart Calculations
  - Session Management
- [x] Payments App _(Implemented but commented out in settings)_
  - Payment Methods
  - Transaction Management
  - Refund Processing
  - Payment Gateway Integration
- [ ] Analytics App
  - Sales Reports
  - Customer Analytics
  - Inventory Reports
  - Performance Metrics

## Notes on Architecture

- **Customer functionality** is implemented in the Core app rather than a separate app
- **Tax, Discount, and Shipping** features are built into the Orders app models
- **Payments** app exists but is currently commented out in settings (ready for activation)
- No separate Shipping app - shipping is handled within Orders app

## Models

### Core

- [x] User Model
  - Extended Django User with e-commerce fields
- [x] Address Model
  - Support for multiple address types
- [x] Configuration Model
  - Store settings and preferences

### Products

- [x] Product Model
  - Base product information
  - SEO fields
  - Status (draft, active, archived)
- [x] ProductVariant Model
  - SKU, barcode
  - Price, compare at price
  - Inventory tracking
- [x] ProductOption Model
  - Color, size, material etc
- [x] ProductImage Model
  - Image management
  - Alt text, position
- [x] Category Model
  - Hierarchical categories
  - SEO fields
- [x] Collection Model
  - Curated product groups
  - Automated collections

### Orders

- [x] Order Model
  - Order details
  - Status management
  - Financial details
- [x] OrderLineItem Model
  - Product variants
  - Quantities
  - Prices at time of order
- [x] FulfillmentOrder Model
  - Shipping details
  - Tracking information
- [x] OrderNote Model
  - Internal and customer notes

### Cart

- [x] Cart Model
  - Session management
  - Expiry handling
- [x] CartItem Model
  - Product variants
  - Quantities
  - Price calculations

### Core (Customer Models)

- [x] Customer Model
  - Extended user profile
  - Preferences and groups
- [x] CustomerGroup Model
  - Segmentation
  - Special pricing
- [x] Address Model
  - Multiple addresses per user
  - Address validation
- [x] CustomerFeedback Model
  - Customer feedback and ratings

### Orders (includes Tax, Discounts, Payments)

- [x] Tax Model _(in Orders app)_
  - Tax calculations
  - Order tax tracking
- [x] Discount Model _(in Orders app)_
  - Order discounts
  - Discount rules
- [x] Payment Model _(in Orders app)_
  - Order payment tracking
- [x] Refund Model _(in Orders app)_
  - Refund processing
  - Status tracking
- [x] Fulfillment Model _(in Orders app)_
  - Shipping details
  - Tracking information

### Payments App (Standalone - commented out)

- [x] PaymentMethod Model
  - Payment gateway info
  - Credentials
- [x] Transaction Model
  - Payment processing
  - Status tracking
- [x] Refund Model _(duplicate with Orders)_
  - Refund processing
  - Status tracking

### Not Yet Implemented

- [ ] Analytics Models
  - Sales reports
  - Performance metrics
- [ ] Coupon Model _(advanced discount features)_
  - Code generation
  - Usage tracking
- [ ] GiftCard Model
  - Balance tracking
  - Usage history

## API Controllers (using django-ninja-extra)

### Core

- [x] Authentication Controller
  - JWT token management
  - Permission checking
- [x] User Controller
  - User management
  - Profile updates
- [x] Customer Controller
  - Customer profile management
  - Address management

### Products

- [x] Product Controller
  - CRUD operations
  - Variant management
- [x] Category Controller
  - Hierarchical management
- [x] Collection Controller
  - Collection management
  - Product assignments
- [x] Tag Controller
  - Tag management
- [x] ProductOption Controller
  - Option management
- [x] Attribute Controller
  - Attribute management
- [x] Bundle Controller
  - Bundle management
- [x] Review Controller
  - Review management
- [x] Inventory Controller
  - Inventory management
- [x] Price Controller
  - Price management

### Orders

- [x] Order Controller
  - Order processing
  - Status updates
- [x] Fulfillment Controller
  - Shipping management
  - Tracking updates
- [x] OrderNote Controller
  - Note management
- [x] OrderHistory Controller
  - History tracking
- [x] Payment Controller
  - Payment processing
- [x] Refund Controller
  - Refund handling
- [x] Tax Controller
  - Tax calculation

### Cart

- [x] Cart Controller
  - Cart management
  - Item updates
- [x] CartItem Controller
  - Item management
  - Price calculations

### Core (includes Customer functionality)

- [x] Customer Controller
  - Profile management
  - Address management
- [x] CustomerGroup Controller
  - Group management
  - Member assignments

### Payments

- [x] Payment Controller
  - Payment processing
  - Refund handling
- [x] PaymentMethod Controller
  - Method management
  - Gateway configuration

### Built into Orders App

- [x] Tax Controller
  - Tax calculations
  - Order tax management
- [x] Refund Controller
  - Refund processing
  - Status tracking
- [x] Payment Controller
  - Order payment processing
- [x] Fulfillment Controller
  - Shipping management
  - Tracking updates

### Not Yet Implemented

- [ ] Discount Controller _(Models exist in Orders app)_
  - Discount management
  - Validation rules
- [ ] Analytics Controller
  - Sales reports
  - Performance metrics

## Schemas (using Pydantic)

### Core

- [x] UserSchema
- [x] AddressSchema
- [x] ConfigurationSchema

### Products

- [x] ProductSchema
- [x] ProductVariantSchema
- [x] ProductOptionSchema
- [x] CategorySchema
- [x] CollectionSchema
- [x] TagSchema
- [x] AttributeSchema
- [x] BundleSchema
- [x] ReviewSchema

### Orders

- [x] OrderSchema
- [x] OrderLineItemSchema
- [x] FulfillmentSchema
- [x] OrderNoteSchema
- [x] OrderHistorySchema

### Cart

- [x] CartSchema
- [x] CartItemSchema
- [x] CartCalculationSchema

### Core (Customer Schemas)

- [x] CustomerSchema
- [x] CustomerGroupSchema _(Note: CustomerGroup is in Core app)_
- [x] AddressSchema
- [x] CustomerFeedbackSchema

### Orders (Tax, Payment, Fulfillment Schemas)

- [x] TaxSchema
- [x] PaymentSchema _(Orders app)_
- [x] RefundSchema
- [x] FulfillmentSchema
- [x] DiscountSchema _(basic implementation)_

### Payments App (Standalone Schemas)

- [x] PaymentMethodSchema
- [x] TransactionSchema
- [x] RefundSchema _(duplicate with Orders)_

### Not Yet Implemented

- [ ] AdvancedDiscountSchema
- [ ] CouponSchema
- [ ] GiftCardSchema
- [ ] AnalyticsSchema

## Additional Tasks

### Documentation

- [x] API Documentation using OpenAPI/Swagger
- [x] Model Documentation
- [x] Setup Instructions
- [x] Deployment Guide

### Testing

- [x] Unit Tests for Models
- [x] Integration Tests for Controllers
- [x] API Tests
- [ ] Performance Tests

### Development Tools

- [x] Data Seeding Scripts (comprehensive generators)
- [x] Development Environment Setup (Docker + uv)
- [x] Docker Configuration (dev + prod)
- [x] Enhanced Development Scripts (dev_setup.sh, code_quality.sh, etc.)
- [x] Hot Reloading Development Server
- [x] Comprehensive Test Factories
- [ ] CI/CD Pipeline

### Security

- [x] API Authentication (JWT with Django Ninja JWT)
- [x] Rate Limiting (built-in decorators)
- [x] Input Validation (Pydantic schemas)
- [x] Data Encryption (Django defaults)
- [x] RBAC Permissions (role-based access control)
- [x] CORS Configuration
- [ ] PCI Compliance (for payments)

### Monitoring & Caching

- [x] Error Logging (comprehensive decorators)
- [x] Performance Monitoring (with decorators)
- [x] Audit Logging (AbstractBaseModel tracking)
- [x] Redis Caching System (advanced with versioning)
- [x] Cache Management Commands
- [x] Cache Warming and Preloading
- [ ] Analytics Integration

## Advanced Features

- [x] Multi-currency support
- [x] Multi-language support
- [x] Inventory management with low stock alerts
- [x] Product bundling and kitting
- [x] Dynamic pricing rules
- [x] Customer segmentation
- [x] Abandoned cart recovery
- [x] Order tracking and notifications
- [x] Product reviews and ratings
- [x] SEO optimization for products
- [ ] Recommendation engine
- [ ] A/B testing framework
- [ ] Subscription management
- [ ] Loyalty program
- [ ] Gift cards and store credit
- [ ] Marketplace support (multiple vendors)
- [ ] Dropshipping integration
- [ ] Headless commerce API
- [ ] Omnichannel inventory management
- [ ] Advanced analytics and reporting

---

## 📊 Implementation Status Summary

### ✅ Fully Implemented (95% complete)

- **Core App**: Authentication, Users, Customers, Addresses, Feedback
- **Products App**: Full product management with variants, categories, reviews, inventory
- **Cart App**: Complete shopping cart functionality with session management
- **Orders App**: Comprehensive order management including tax, discounts, payments, fulfillment
- **Caching System**: Advanced Redis caching with versioning and warming
- **Development Tools**: Complete Docker setup, scripts, and testing infrastructure

### 🚧 Partially Implemented

- **Payments App**: Exists but commented out in settings (standalone payment processing)
- **Advanced Features**: Most ecommerce features implemented, ML features planned

### ❌ Not Yet Implemented

- **Analytics App**: Sales reports, customer analytics, inventory reports
- **Advanced Discounts**: Coupon codes, gift cards (basic discounts exist in Orders)
- **CI/CD Pipeline**: Deployment automation
- **ML Features**: Recommendation engine, A/B testing, advanced analytics

### 🏗️ Architecture Notes

- **Modular Design**: Features are logically separated but efficiently organized
- **No Over-Engineering**: Customer, Tax, Shipping built into relevant apps rather than separate apps
- **Production Ready**: Comprehensive caching, error handling, testing, and development tools
- **Scalable**: Ready for ML integration and advanced features

---

## 🔥 Audit-Driven Backlog (Priority Order)

### P1 — Critical (portfolio credibility blockers)

- [ ] **Enable Payments app + wire Stripe webhooks**
  - Uncomment payments app in `INSTALLED_APPS`
  - Create migrations for payments models
  - Add inbound Stripe webhook endpoint (`/webhooks/stripe/`)
  - Handle key events: `payment_intent.succeeded`, `payment_intent.failed`, `charge.refunded`, `customer.subscription.*`
  - Add webhook signature verification
  - Write tests for webhook handlers

- [ ] **Fix Analytics app (currently a ghost)**
  - Create migrations for all analytics models
  - Verify analytics is in `INSTALLED_APPS`
  - Add `generate_analytics_data` management command
  - Write tests for all analytics controllers (currently 0)
  - Add analytics data aggregation Celery tasks

- [ ] **Add Sentry error tracking**
  - Add `sentry-sdk[django,celery]` dependency
  - Configure in `api/settings/common.py` (gated by `SENTRY_DSN` env var)
  - Add Sentry to Celery signal handlers
  - Add `SENTRY_DSN` to `.env.example`
  - Every other project in this portfolio has Sentry — this one needs it

- [ ] **Add service layer to core apps**
  - Create `services/` directory per app (core, products, orders, cart)
  - Extract business logic out of controllers into service classes
  - Follow `BaseService[T]` / `CRUDService[T]` pattern from boilerplate
  - Controllers become thin HTTP adapters; services become testable units

- [ ] **Coupon / promo code system**
  - Add `Coupon` model (code, discount type, value, usage limit, expiry, min order value)
  - Add `CouponUsage` model (track per-customer usage)
  - `CouponController` with validate/apply/list/CRUD endpoints
  - Integration with cart and order checkout flow
  - Tests for all coupon validation logic

### P2 — Medium (distinguish from tutorial projects)

- [ ] **Structured logging (python-json-logger)**
  - Add `python-json-logger` dependency
  - Replace default Django logging config in `common.py` with JSON formatter for prod
  - Add request ID middleware so logs are traceable per request
  - Keep human-readable format for dev

- [ ] **Celery tasks — actually implement them**
  - `send_order_confirmation_email` task (orders app)
  - `send_low_stock_alert` task (products app, triggered when inventory < threshold)
  - `send_abandoned_cart_email` task (cart app, triggered N hours after cart inactivity)
  - `aggregate_daily_analytics` task (analytics app, runs nightly via celery-beat)
  - `process_refund` task (payments app, async refund via Stripe)

- [ ] **Dead Letter Queue for Celery tasks**
  - Add DLQ model to store failed task metadata
  - Add management command to inspect/retry DLQ entries
  - Add API endpoints: `GET /api/tasks/dlq/`, `POST /api/tasks/dlq/{id}/retry`
  - Critical for payment-adjacent tasks where silent failure is unacceptable

- [ ] **CI/CD deploy stage**
  - Add Railway or Render deploy step to `.github/workflows/ci.yml`
  - Deploy only on push to `main` after lint + test pass
  - Add staging environment job
  - Document deploy config in README

- [ ] **Clean up duplicate management commands**
  - Consolidate `generate_products.py`, `generate_product_data.py`, `generate_products_data.py` → single `generate_products.py`
  - Audit all apps for similar redundancy
  - Update `generate_all_data.py` references

### P3 — Nice-to-have (separates solid from impressive)

- [ ] **Webhook app (outbound webhooks)**
  - `Webhook` model (endpoint URL, events subscribed, secret, active flag)
  - `WebhookDelivery` model (request/response log, retry count)
  - Celery task to deliver webhook events with retry + exponential backoff
  - API to register/manage webhook endpoints
  - Sign payloads with HMAC-SHA256

- [ ] **OpenTelemetry observability (optional install group)**
  - Add `opentelemetry-sdk`, `opentelemetry-instrumentation-django`, `opentelemetry-instrumentation-celery` as optional deps
  - Add `core/observability/` module with trace spans and Prometheus metrics
  - Gate behind `OTEL_ENABLED` env var so it's opt-in
  - Export to Jaeger or OTLP endpoint

- [ ] **Feature flags system**
  - `FeatureFlag` model (name, enabled, rollout_percentage, variants)
  - `FeatureFlagService` with `is_enabled(flag, user)` and `get_variant(flag, user)`
  - Middleware to attach active flags to request context
  - Admin CRUD + toggle endpoints
  - Use for safe rollout of new checkout flow, new pricing logic, etc.

- [ ] **Gift cards / store credit**
  - `GiftCard` model (code, balance, issued_to, expires_at, status)
  - `GiftCardTransaction` model (usage history)
  - `GiftCardController` with issue/redeem/balance endpoints
  - Integration with cart checkout flow

- [ ] **Subscription management**
  - `Subscription` model (plan, status, billing cycle, Stripe subscription ID)
  - `SubscriptionPlan` model (name, price, interval, features)
  - Wire to Stripe Billing API
  - Handle `customer.subscription.updated/deleted` webhooks
  - Upgrade/downgrade/cancel endpoints

- [ ] **Rate limiting on auth endpoints**
  - Add `django-ratelimit` or custom throttle decorator to login, OTP, password reset
  - Brute force protection (lock account after N failed attempts)
  - Track attempts in Redis with TTL

- [ ] **API versioning**
  - Add `/api/v1/` prefix to all routes
  - Configure versioning in `api/urls.py`
  - Document deprecation strategy

### P4 — Future / ML

- [ ] Recommendation engine (collaborative filtering or content-based)
- [ ] A/B testing framework
- [ ] pgvector for semantic product search
- [ ] Inventory demand forecasting
- [ ] Dynamic pricing rules engine
- [ ] Marketplace / multi-vendor support
