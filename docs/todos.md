# TODO / Roadmap

## Current State (verified 2026-08-15)

- 204 tests pass
- 58% coverage across 11,046 statements
- All apps enabled: core, products, cart, orders, analytics, payments,
  coupons, outbound_webhooks, feature_flags, gift_cards, subscriptions
- CI/CD runs lint (ruff), tests (pytest on Postgres 17 + Redis 7.2), builds
  a GHCR image, and deploys via SSH on push to main
- Stripe webhook endpoint active with signature verification and idempotent
  event log
- Service layers: OrderService, CartService, PaymentService, CouponService,
  GiftCardService, SubscriptionService, FeatureFlagService, WebhookService
- N+1 query guards: order and product list query-count tests
- Passwordless login (OTP) with rate throttling on login
- OpenTelemetry setup gated by `OTEL_ENABLED`
- Sentry, structured logging, Celery + beat, and DLQ wired

## Roadmap

Four themes, in owner-approved order. Theme A is last on purpose: ship
visible features first, harden and test after.

### Theme B — API platform features

Senior-level API design signals. Highest portfolio value next.

- [ ] API versioning
  - Add `/api/v1/` prefix to all routes
  - Configure versioning in `api/urls.py`
  - Document the deprecation policy in README
- [ ] Idempotent order creation
  - Accept `Idempotency-Key` header on order create
  - Replay protection: return the original order, never a duplicate
  - Persist keys with expiry; clean up stale keys
  - Tests: same key twice returns same order; different keys create
    different orders; missing key still works
- [ ] Formal order state machine
  - Define allowed transitions per status in `orders/models/choices.py`
  - Enforce transitions in OrderService, not controllers
  - Reject invalid transitions with 409
  - Record every transition in order history
  - Tests: happy path, invalid jump, staff override, history entries

### Theme C — New commerce features

Visible features that complete the storefront story.

- [ ] Wishlist app
  - `Wishlist` model: customer, product variants
  - `WishlistItem` model with created_at ordering
  - Controller: list, add, remove, clear, check membership
  - Use the existing `wishlist_updated` error message constant
  - Tests: ownership, duplicates, remove non-member item
- [ ] Loyalty points
  - Points awarded per order total; configurable rate
  - Redeem points against an order; points ledger with history
  - Controller: balance, history, redeem
  - Celery task to credit points after order completion
  - Tests: earn, redeem, insufficient balance, concurrent redemption
- [ ] Search enhancements
  - Weighted full-text search on products (name > description > tags)
  - Highlight snippets and relevance ordering
  - Later: pgvector semantic search as a P4/ML item

### Theme D — Performance and observability

Prove scalability with numbers.

- [ ] Load tests
  - Add locust or k6 scenario: product list, product detail, cart add,
    checkout, order create
  - Run against Docker stack; capture latency percentiles and error rates
  - Publish benchmark numbers in README with hardware note
- [ ] Request-ID middleware
  - Generate or accept `X-Request-ID`
  - Echo it in responses; include it in every log line
  - Correlate Celery tasks with the originating request ID
- [ ] Deeper health checks
  - `api/healthcheck.py` currently 20% covered
  - Add Redis ping, Celery worker liveness, and migration drift checks
  - Distinguish liveness vs readiness endpoints
  - Tests for each probe

### Theme A — Production hardening and coverage

Do last, per owner decision. Starts with a dead-code audit so test effort
targets live paths only.

- [ ] Dead-code audit
  - Delete `api/search_filters.py` (233 stmts, zero imports)
  - Delete `api/pagination.py` (158 stmts, zero imports)
  - Delete `api/rbac_permissions.py` (200 stmts, zero imports)
  - Live equivalents: `search_and_filter`, `paginate_response`,
    `require_permissions` in `api/decorators.py`
  - Confirm nothing references them; update `docs/resume-prompt.md`
- [ ] Coverage push 58% -> 80%+
  - RBAC permission classes in `api/permissions.py` (19%)
  - Live search/filter and pagination paths in `api/decorators.py` (67%)
  - Cache system: `core/cache/*` versioning, warming, signals, preload (0%)
  - Celery tasks and DLQ retry path in every app (0%)
  - Controllers: refund (0%), inventory (0%), price (0%), cart_item (43%),
    analytics sales report (50%)
  - Health checks: `api/healthcheck.py` (20%)
  - Email service: `core/services/email/*` (0%)
  - Analytics: `generate_analytics` command (0%), `analytics/tasks.py` (0%),
    controller tests for sales reports
  - Management commands: generate_*, cache_ops, setup_rbac (0%)

## Later / ML ideas (P4)

- Recommendation engine (content-based or collaborative)
- A/B testing framework (feature_flags has rollout %, extend it)
- pgvector semantic product search
- Inventory demand forecasting
- Dynamic pricing rules engine
- Marketplace / multi-vendor support

## Prior backlog (done)

Everything below shipped and passes tests. Kept as an audit trail.

- Payments app enabled; Stripe webhooks with signature verification and
  idempotent event log
- Coupon/promo system: models, service layer, 24 tests
- Gift cards: balance, transactions, redemption
- Subscriptions: plans, customer subscriptions, Stripe billing wiring
- Outbound webhooks: endpoints, HMAC signing, retries, delivery log
- Feature flags: rollout %, service, admin CRUD
- Rate limiting on auth endpoints
- OpenTelemetry observability (opt-in)
- Sentry for Django + Celery
- Structured JSON logging
- Real Celery tasks: order confirmation, low-stock alert, abandoned cart,
  analytics aggregation, refund processing
- Dead Letter Queue for failed tasks
- CI/CD: lint, test, GHCR build, SSH deploy
- Service-layer extraction for orders, cart, payments
- N+1 query tests for orders and products
