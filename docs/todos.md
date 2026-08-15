# TODO / Roadmap

## Current State (verified 2026-08-15)

- 361 tests pass
- 61% coverage across 11,838 statements
- All apps enabled: core, products, cart, orders, analytics, payments,
  coupons, outbound_webhooks, feature_flags, gift_cards, subscriptions,
  wishlist, loyalty
- CI/CD runs lint (ruff), tests (pytest on Postgres 17 + Redis 7.2), builds
  a GHCR image, and deploys via SSH on push to main
- Stripe webhook endpoint active with signature verification and idempotent
  event log
- Service layers: OrderService, CartService, PaymentService, CouponService,
  GiftCardService, SubscriptionService, FeatureFlagService, WebhookService,
  WishlistService, LoyaltyService, ProductService
- Weighted full-text product search (name A / description B / tags C)
  with SearchRank relevance ordering
- Loyalty points ledger with earn-on-COMPLETED Celery task and redeem
- Wishlist app with per-customer wishlists and idempotent add
- N+1 query guards: order and product list query-count tests
- OpenTelemetry setup gated by `OTEL_ENABLED`
- X-Request-ID correlation: middleware accepts/generates/echoes the
  header, a logging filter injects it into every record, and Celery task
  headers carry it to worker logs via a `task_prerun` signal
- Health checks cover redis PING, Celery worker liveness
  (`control.ping`), migration drift, and SMTP; readiness gates on
  database + redis + celery; `/health/all/` no longer permanently
  unhealthy
- Locust benchmark suite (`loadtests/`) with real p50/p95/p99 and error
  rates published in the README (Apple M2 Pro, Docker Postgres 17 +
  Redis 7.2)

## Roadmap

Four themes, in owner-approved order. Theme A is last on purpose: ship
visible features first, harden and test after.

### Theme B — API platform features

Senior-level API design signals. Highest portfolio value next.

Deferred to v2: API versioning with an `/api/v1/` prefix and a documented
deprecation policy. Not part of the current plan.
- [x] Idempotent order creation
  - `IdempotencyKey` model: hashed key, user-scoped, request hash, 24h TTL
  - `Idempotency-Key` header accepted on order create; replay returns the
    original order with 200; different payload with same key returns 409
  - Daily Celery cleanup task for expired keys
  - Also fixed: order create now generates `order_number` (was empty and
    unique-constrained), and non-staff users must own the customer
- [x] Formal order state machine
  - `ORDER_STATUS_TRANSITIONS` map in `orders/models/choices.py`
  - `OrderService.transition_order` enforces it; invalid jumps raise 409
  - Staff may force transitions (bypass map, still recorded in history)
  - Every transition writes an `OrderHistory` row (old + new status)
  - submit/cancel/update, fulfillment create/update/delete/ship/cancel,
    and refund paths all route through the machine
  - `OrderSchema.history` now serializes `OrderHistorySchema`

### Theme C — New commerce features

Visible features that complete the storefront story.

- [x] Wishlist app
  - `Wishlist` model: one per customer, with items
  - `WishlistItem` model: variant, quantity, notes; unique per
    (wishlist, variant); created_at ordering
  - Controller: list, add, remove, clear, check membership; ownership
    resolved strictly from request.user
  - Uses the existing `wishlist_updated` error message constant
  - Tests: ownership, duplicates, remove non-member item (30 tests)
- [x] Loyalty points
  - Points awarded per order total; rate constant
    `LOYALTY_POINTS_PER_DOLLAR`
  - Redeem points against an order; signed ledger with history
  - Controller: balance, history, redeem
  - Celery task credits points after order completion, wired into
    `OrderService.transition_order`; dedupe per order (partial unique
    constraint)
  - Tests: earn, redeem, insufficient balance, no double credit (28
    tests)


### Theme D — Performance and observability

Prove scalability with numbers.

- [x] Load tests
  - Locust scenario suite (`loadtests/locustfile.py`): product list,
    product detail, cart add, checkout (create + submit), order create
  - Ran headless against the dev stack (Docker Postgres 17 + Redis 7.2):
    20 users, 2/s ramp, 5 min; 0.0% error rate over 3,320 requests
  - Real p50/p95/p99 per endpoint published in the README Benchmarks
    section with the Apple M2 Pro hardware note; `make bench` re-runs it
- [x] Request-ID middleware
  - `X-Request-ID` accepted, sanitized, generated (`uuid4().hex`), and
    echoed on every response; stored on `request.request_id`
  - `RequestIdLogFilter` injects the id into every log record (JSON and
    console); `{request_id}` in the console format
  - Celery correlation: `credit_order_points` dispatch carries
    `x_request_id` in task headers; `task_prerun`/`task_postrun`
    signals restore and clear the id in worker logs
  - Tests: echo, generate, sanitize/cap, caplog request_id, worker
    signal restore/clear, task log correlation (6 tests)
- [x] Deeper health checks
  - `api/healthcheck.py` 20% -> 70% covered
  - Redis probe adds a direct PING; Celery liveness via
    `control.ping(timeout=2)`; migration drift probes
    `MigrationLoader.disk_migrations` against
    `MigrationRecorder.applied_migrations()`; SMTP probe skips when no
    SMTP backend is configured
  - `skipped` services no longer flip `/health/all/` to unhealthy
    (email/s3/stripe are skipped in dev); readiness now gates on
    database + redis + celery; liveness stays process-alive
  - Tests: per-probe healthy/unhealthy, `/health/`, `/readiness/` 200 +
    503, `/liveness/`, unknown service (15 tests)

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
- [ ] Coverage push 61% -> 80%+
  - RBAC permission classes in `api/permissions.py` (19%)
  - Live search/filter and pagination paths in `api/decorators.py` (65%)
  - Cache system: `core/cache/*` versioning, warming, signals, preload (0%)
  - Celery tasks and DLQ retry path in every app (0%)
  - Controllers: refund (0%), inventory (0%), price (0%), cart_item (43%),
    analytics sales report (50%)
  - Health checks: `api/healthcheck.py` (70% — probes from Theme D; the
    remaining gap is the monitoring/summary paths)
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
