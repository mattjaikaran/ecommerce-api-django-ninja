# Resume Prompt — Ecommerce API Update

Paste this at the start of a new session to restore full context.

---

## Project

`~/dev/ecommerce/ecommerce-api-update` — Django 5.2 + Django Ninja + Django Ninja Extra ecommerce REST API. Portfolio / public repo project. Goal: make it look genuinely production-ready, not a tutorial clone.

**Stack:** Python 3.13, uv, Django Ninja Extra (class-based controllers), Pydantic v2, PostgreSQL, Redis, Celery, Django Unfold admin, JWT auth, Stripe, AWS S3, Docker.

## What's built (solid, don't touch)

- `core/` — auth (JWT), users, customers, addresses, RBAC, OTP, Redis caching system
- `products/` — products, variants, options, categories, collections, reviews, tags, attributes, bundles, price/inventory history
- `orders/` — orders, line items, fulfillment, payments, refunds, discounts, taxes, notes, history
- `cart/` — cart, cart items, session management
- `api/` — decorators, RBAC permissions, search/filter, pagination, exceptions, health checks, Celery config
- Docker (dev + prod), Nginx, Makefile, CI (lint + test), pytest with factory-boy

## Audit findings — work in this order (see docs/todos.md for full detail)

### P1 — Critical (in progress / up next)
1. **Enable Payments app + wire Stripe webhooks** ← START HERE
   - Uncomment `payments` in `INSTALLED_APPS` (api/settings/common.py)
   - Run `makemigrations payments` + `migrate`
   - Add inbound Stripe webhook endpoint at `/webhooks/stripe/`
   - Handle: `payment_intent.succeeded`, `payment_intent.failed`, `charge.refunded`, `customer.subscription.*`
   - Add webhook signature verification using `stripe.WebhookSignature`
   - Write tests

2. **Fix Analytics app (ghost app — models exist, zero migrations, zero tests)**
   - Create migrations for all analytics models
   - Add `generate_analytics_data` management command
   - Write tests for all analytics controllers

3. **Add Sentry** (`sentry-sdk[django,celery]`)
   - Gate on `SENTRY_DSN` env var
   - Configure in `api/settings/common.py`

4. **Add service layer** — extract business logic from controllers into `services/` per app

5. **Coupon / promo code system** — `Coupon` + `CouponUsage` models, controller, cart integration

### P2 — Medium
6. Structured logging (python-json-logger, JSON in prod)
7. Implement real Celery tasks (order confirmation email, low stock alert, abandoned cart, daily analytics)
8. Dead Letter Queue for failed Celery tasks
9. CI/CD deploy stage (Railway or Render)
10. Clean up duplicate management commands in products app

### P3 — Nice-to-have
11. Outbound webhook app
12. OpenTelemetry (optional install group)
13. Feature flags system
14. Gift cards / store credit
15. Subscription management (Stripe Billing)
16. Rate limiting / brute force protection on auth

## Key file locations

| Thing | Path |
|-------|------|
| Settings | `api/settings/common.py`, `dev.py`, `prod.py` |
| URL routing | `api/urls.py` |
| Installed apps | `api/settings/common.py` → `INSTALLED_APPS` |
| Payments app | `payments/` (currently commented out) |
| Analytics app | `analytics/` (no migrations, no tests) |
| Celery tasks | `core/tasks.py` (82 lines, near empty) |
| Decorators | `api/decorators.py` |
| RBAC | `api/rbac_permissions.py` |
| Full backlog | `docs/todos.md` |
| Boilerplate ref | `~/dev/django-ninja-boilerplate` |
