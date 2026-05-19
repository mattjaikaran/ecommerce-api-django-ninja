# 🏗️ Django Ecommerce API Architecture

This document provides a comprehensive overview of the Django Ecommerce API architecture, including system design, data flow, and component interactions.

## 📋 Table of Contents

- [System Overview](#system-overview)
- [Architecture Patterns](#architecture-patterns)
- [Core Components](#core-components)
- [Data Flow](#data-flow)
- [API Design](#api-design)
- [Database Design](#database-design)
- [Security Architecture](#security-architecture)
- [Deployment Architecture](#deployment-architecture)

## 🎯 System Overview

The Django Ecommerce API is built using modern architectural patterns to ensure scalability, maintainability, and performance.

```mermaid
graph TB
    subgraph "Client Layer"
        WEB[Web Frontend]
        MOBILE[Mobile App]
        ADMIN[Admin Panel]
    end

    subgraph "API Gateway"
        NGINX[Nginx Reverse Proxy]
        LB[Load Balancer]
    end

    subgraph "Application Layer"
        DJANGO[Django API Server]
        CELERY[Celery Workers]
        BEAT[Celery Beat Scheduler]
    end

    subgraph "Data Layer"
        POSTGRES[(PostgreSQL)]
        REDIS[(Redis Cache)]
        S3[(AWS S3)]
    end

    subgraph "External Services"
        STRIPE[Stripe Payments]
        EMAIL[Email Service]
        ANALYTICS[Analytics]
    end

    WEB --> NGINX
    MOBILE --> NGINX
    ADMIN --> NGINX

    NGINX --> LB
    LB --> DJANGO

    DJANGO --> POSTGRES
    DJANGO --> REDIS
    DJANGO --> S3
    DJANGO --> CELERY

    CELERY --> POSTGRES
    CELERY --> REDIS
    CELERY --> EMAIL

    BEAT --> CELERY

    DJANGO --> STRIPE
    DJANGO --> ANALYTICS

    style DJANGO fill:#e1f5fe
    style POSTGRES fill:#f3e5f5
    style REDIS fill:#fff3e0
```

## 🔧 Architecture Patterns

### 1. Layered Architecture

```mermaid
graph TB
    subgraph "Presentation Layer"
        API[REST API Endpoints]
        SCHEMAS[Pydantic Schemas]
        SERIALIZERS[DRF Serializers]
    end

    subgraph "Business Logic Layer"
        CONTROLLERS[Controllers]
        SERVICES[Business Services]
        VALIDATORS[Data Validators]
    end

    subgraph "Data Access Layer"
        MODELS[Django Models]
        MANAGERS[Model Managers]
        REPOSITORIES[Repository Pattern]
    end

    subgraph "Infrastructure Layer"
        DATABASE[(Database)]
        CACHE[(Cache)]
        STORAGE[(File Storage)]
        QUEUE[(Task Queue)]
    end

    API --> CONTROLLERS
    SCHEMAS --> CONTROLLERS
    SERIALIZERS --> CONTROLLERS

    CONTROLLERS --> SERVICES
    SERVICES --> VALIDATORS

    SERVICES --> MODELS
    MODELS --> MANAGERS
    MANAGERS --> REPOSITORIES

    REPOSITORIES --> DATABASE
    SERVICES --> CACHE
    SERVICES --> STORAGE
    SERVICES --> QUEUE
```

### 2. Domain-Driven Design (DDD)

```mermaid
graph LR
    subgraph "Core Domain"
        PRODUCTS[Products Domain]
        ORDERS[Orders Domain]
        CUSTOMERS[Customers Domain]
    end

    subgraph "Supporting Domains"
        CART[Cart Domain]
        PAYMENTS[Payments Domain]
        INVENTORY[Inventory Domain]
        COUPONS[Coupons Domain]
        GIFT_CARDS[Gift Cards Domain]
        SUBSCRIPTIONS[Subscriptions Domain]
    end

    subgraph "Generic Domains"
        AUTH[Authentication]
        NOTIFICATIONS[Notifications]
        ANALYTICS[Analytics]
        WEBHOOKS[Outbound Webhooks]
        FLAGS[Feature Flags]
    end

    PRODUCTS --> CART
    CART --> ORDERS
    CUSTOMERS --> ORDERS
    ORDERS --> PAYMENTS
    PRODUCTS --> INVENTORY
    COUPONS --> ORDERS
    GIFT_CARDS --> ORDERS
    SUBSCRIPTIONS --> PAYMENTS

    AUTH --> CUSTOMERS
    ORDERS --> NOTIFICATIONS
    ORDERS --> ANALYTICS
    ORDERS --> WEBHOOKS
    FLAGS --> PRODUCTS
    FLAGS --> PAYMENTS
```

## 🧩 Core Components

### Application Structure

```mermaid
graph TB
    subgraph "Django Project"
        API[api/ - Core Configuration]

        subgraph "Domain Apps"
            CORE[core/ - User Management]
            PRODUCTS[products/ - Product Catalog]
            CART[cart/ - Shopping Cart]
            ORDERS[orders/ - Order Management]
            PAYMENTS[payments/ - Payment Processing]
            COUPONS[coupons/ - Promo Codes]
            GIFT_CARDS[gift_cards/ - Gift Cards]
            SUBSCRIPTIONS[subscriptions/ - Recurring Billing]
            WEBHOOKS[outbound_webhooks/ - Event Delivery]
            FLAGS[feature_flags/ - Feature Toggles]
            ANALYTICS[analytics/ - Event Tracking]
        end

        subgraph "Supporting Components"
            UTILS[api/utils/ - Utility Functions]
            CONFIG[api/config/ - Configuration]
            SCRIPTS[scripts/ - Development Tools]
        end
    end

    API --> CORE
    API --> PRODUCTS
    API --> CART
    API --> ORDERS
    API --> PAYMENTS
    API --> COUPONS
    API --> GIFT_CARDS
    API --> SUBSCRIPTIONS
    API --> WEBHOOKS
    API --> FLAGS
    API --> ANALYTICS

    API --> UTILS
    API --> CONFIG

    CORE --> UTILS
    PRODUCTS --> UTILS
    CART --> UTILS
    ORDERS --> UTILS
    PAYMENTS --> UTILS
    COUPONS --> UTILS
    SUBSCRIPTIONS --> UTILS
```

### Model Architecture

```mermaid
graph TB
    subgraph "Core Models"
        USER[User]
        CUSTOMER[Customer]
        ADDRESS[Address]
        ABSTRACT[AbstractBaseModel]
    end

    subgraph "Product Models"
        PRODUCT[Product]
        VARIANT[ProductVariant]
        CATEGORY[Category]
        ATTRIBUTE[ProductAttribute]
    end

    subgraph "Cart Models"
        CART[Cart]
        CART_ITEM[CartItem]
    end

    subgraph "Order Models"
        ORDER[Order]
        ORDER_ITEM[OrderLineItem]
        FULFILLMENT[Fulfillment]
        PAYMENT[Payment]
    end

    ABSTRACT --> USER
    ABSTRACT --> CUSTOMER
    ABSTRACT --> ADDRESS
    ABSTRACT --> PRODUCT
    ABSTRACT --> CART
    ABSTRACT --> ORDER

    USER --> CUSTOMER
    USER --> ADDRESS
    CUSTOMER --> CART
    CUSTOMER --> ORDER

    PRODUCT --> VARIANT
    PRODUCT --> CATEGORY
    VARIANT --> CART_ITEM
    VARIANT --> ORDER_ITEM

    CART --> CART_ITEM
    ORDER --> ORDER_ITEM
    ORDER --> FULFILLMENT
    ORDER --> PAYMENT
```

## 🌊 Data Flow

### Order Processing Flow

```mermaid
sequenceDiagram
    participant C as Customer
    participant API as Django API
    participant DB as Database
    participant CACHE as Redis
    participant CELERY as Celery
    participant PAYMENT as Payment Gateway
    participant EMAIL as Email Service

    C->>API: Add items to cart
    API->>CACHE: Cache cart state
    API->>C: Cart updated

    C->>API: Proceed to checkout
    API->>DB: Validate inventory
    API->>API: Calculate totals
    API->>C: Checkout summary

    C->>API: Place order
    API->>DB: Create order
    API->>PAYMENT: Process payment
    PAYMENT->>API: Payment response

    alt Payment Success
        API->>DB: Update order status
        API->>CELERY: Queue email task
        API->>CELERY: Queue inventory update
        API->>C: Order confirmation

        CELERY->>EMAIL: Send confirmation email
        CELERY->>DB: Update inventory levels
    else Payment Failed
        API->>DB: Mark order as failed
        API->>C: Payment error
    end
```

### Product Search Flow

```mermaid
sequenceDiagram
    participant C as Customer
    participant API as Django API
    participant CACHE as Redis Cache
    participant DB as Database
    participant SEARCH as Search Engine

    C->>API: Search products
    API->>CACHE: Check cache

    alt Cache Hit
        CACHE->>API: Return cached results
        API->>C: Product results
    else Cache Miss
        API->>DB: Query products
        API->>SEARCH: Enhanced search
        SEARCH->>API: Search results
        API->>DB: Get product details
        DB->>API: Product data
        API->>CACHE: Cache results
        API->>C: Product results
    end
```

## 🔌 API Design

### RESTful API Structure

```mermaid
graph TB
    subgraph "API Endpoints"
        AUTH[/api/v1/auth/]
        PRODUCTS[/api/v1/products/]
        CART[/api/v1/cart/]
        ORDERS[/api/v1/orders/]
        CUSTOMERS[/api/v1/customers/]
        PAYMENTS[/api/v1/payments/]
        COUPONS[/api/v1/coupons/]
        GIFT_CARDS[/api/v1/gift-cards/]
        SUBSCRIPTIONS[/api/v1/subscriptions/]
        WEBHOOKS[/api/v1/webhooks/]
        FLAGS[/api/v1/feature-flags/]
        ANALYTICS[/api/v1/analytics/]
    end

    subgraph "HTTP Methods"
        GET[GET - Retrieve]
        POST[POST - Create]
        PUT[PUT - Update]
        PATCH[PATCH - Partial Update]
        DELETE[DELETE - Remove]
    end

    subgraph "Response Formats"
        JSON[JSON Response]
        PAGINATION[Paginated Lists]
        ERRORS[Error Responses]
    end

    AUTH --> GET
    AUTH --> POST

    PRODUCTS --> GET
    PRODUCTS --> POST
    PRODUCTS --> PUT
    PRODUCTS --> PATCH
    PRODUCTS --> DELETE

    CART --> GET
    CART --> POST
    CART --> PUT
    CART --> DELETE

    ORDERS --> GET
    ORDERS --> POST
    ORDERS --> PATCH

    COUPONS --> GET
    COUPONS --> POST
    COUPONS --> PATCH
    COUPONS --> DELETE

    GIFT_CARDS --> GET
    GIFT_CARDS --> POST
    GIFT_CARDS --> PATCH

    SUBSCRIPTIONS --> GET
    SUBSCRIPTIONS --> POST
    SUBSCRIPTIONS --> PATCH
    SUBSCRIPTIONS --> DELETE

    WEBHOOKS --> GET
    WEBHOOKS --> POST
    WEBHOOKS --> DELETE

    FLAGS --> GET
    FLAGS --> POST
    FLAGS --> PATCH
    FLAGS --> DELETE

    ANALYTICS --> GET

    GET --> JSON
    POST --> JSON
    PUT --> JSON
    PATCH --> JSON
    DELETE --> JSON

    JSON --> PAGINATION
    JSON --> ERRORS
```

### Authentication & Authorization

```mermaid
graph TB
    subgraph "Authentication Methods"
        JWT[JWT Tokens]
        SESSION[Session Auth]
        API_KEY[API Key]
    end

    subgraph "Authorization Levels"
        GUEST[Guest User]
        CUSTOMER[Authenticated Customer]
        STAFF[Staff User]
        ADMIN[Administrator]
    end

    subgraph "Protected Resources"
        PUBLIC[Public Products]
        CART_OPS[Cart Operations]
        ORDER_OPS[Order Operations]
        ADMIN_OPS[Admin Operations]
    end

    JWT --> CUSTOMER
    JWT --> STAFF
    JWT --> ADMIN
    SESSION --> CUSTOMER
    API_KEY --> ADMIN

    GUEST --> PUBLIC
    CUSTOMER --> CART_OPS
    CUSTOMER --> ORDER_OPS
    STAFF --> ADMIN_OPS
    ADMIN --> ADMIN_OPS
```

## 🗄️ Database Design

### Entity Relationship Diagram

```mermaid
erDiagram
    User ||--|| Customer : has
    User ||--o{ Address : owns
    Customer ||--o{ Cart : has
    Customer ||--o{ Order : places

    Cart ||--o{ CartItem : contains
    Product ||--o{ ProductVariant : has
    ProductVariant ||--o{ CartItem : in
    ProductVariant ||--o{ OrderLineItem : in

    Order ||--o{ OrderLineItem : contains
    Order ||--o{ Payment : has
    Order ||--o{ Fulfillment : has
    Order ||--o{ OrderNote : has

    Category ||--o{ Product : categorizes
    Product ||--o{ ProductAttribute : has

    User {
        uuid id PK
        string email UK
        string username UK
        string first_name
        string last_name
        datetime date_joined
        boolean is_staff
        boolean is_superuser
    }

    Customer {
        uuid id PK
        uuid user_id FK
        string phone
        boolean is_default
    }

    Product {
        uuid id PK
        string name
        text description
        string sku UK
        decimal price
        boolean is_active
        datetime created_at
    }

    Order {
        uuid id PK
        uuid customer_id FK
        string status
        decimal subtotal
        decimal tax_amount
        decimal shipping_cost
        decimal total_amount
        datetime created_at
    }
```

### Database Indexes Strategy

```mermaid
graph TB
    subgraph "Primary Indexes"
        PK[Primary Keys - UUID]
        UK[Unique Keys - Email, SKU]
    end

    subgraph "Performance Indexes"
        SEARCH[Search Indexes]
        FILTER[Filter Indexes]
        SORT[Sort Indexes]
    end

    subgraph "Composite Indexes"
        USER_STATUS[User + Status]
        PRODUCT_CATEGORY[Product + Category]
        ORDER_DATE[Order + Date]
    end

    subgraph "Cache Strategy"
        REDIS_CACHE[Redis Caching]
        DB_CACHE[Database Query Cache]
        APP_CACHE[Application Cache]
    end

    PK --> SEARCH
    UK --> FILTER
    SEARCH --> SORT

    FILTER --> USER_STATUS
    FILTER --> PRODUCT_CATEGORY
    FILTER --> ORDER_DATE

    SORT --> REDIS_CACHE
    USER_STATUS --> DB_CACHE
    PRODUCT_CATEGORY --> APP_CACHE
```

## 🔒 Security Architecture

### Security Layers

```mermaid
graph TB
    subgraph "Network Security"
        HTTPS[HTTPS/TLS]
        NGINX_SEC[Nginx Security Headers]
        RATE_LIMIT[Rate Limiting]
    end

    subgraph "Application Security"
        JWT_AUTH[JWT Authentication]
        CSRF[CSRF Protection]
        XSS[XSS Protection]
        SQL_INJ[SQL Injection Prevention]
    end

    subgraph "Data Security"
        ENCRYPTION[Data Encryption]
        HASHING[Password Hashing]
        SENSITIVE[Sensitive Data Masking]
    end

    subgraph "Infrastructure Security"
        SECRETS[Secret Management]
        ENV_VAR[Environment Variables]
        DOCKER_SEC[Docker Security]
    end

    HTTPS --> JWT_AUTH
    NGINX_SEC --> CSRF
    RATE_LIMIT --> XSS

    JWT_AUTH --> ENCRYPTION
    CSRF --> HASHING
    XSS --> SENSITIVE
    SQL_INJ --> SENSITIVE

    ENCRYPTION --> SECRETS
    HASHING --> ENV_VAR
    SENSITIVE --> DOCKER_SEC
```

### Permission System

```mermaid
graph TB
    subgraph "Roles"
        GUEST[Guest]
        CUSTOMER[Customer]
        STAFF[Staff]
        ADMIN[Admin]
        SUPERUSER[Superuser]
    end

    subgraph "Permissions"
        READ[Read Products]
        CART_MANAGE[Manage Cart]
        ORDER_CREATE[Create Orders]
        ORDER_MANAGE[Manage Orders]
        PRODUCT_MANAGE[Manage Products]
        USER_MANAGE[Manage Users]
        SYSTEM_ADMIN[System Admin]
    end

    GUEST --> READ

    CUSTOMER --> READ
    CUSTOMER --> CART_MANAGE
    CUSTOMER --> ORDER_CREATE

    STAFF --> READ
    STAFF --> CART_MANAGE
    STAFF --> ORDER_CREATE
    STAFF --> ORDER_MANAGE
    STAFF --> PRODUCT_MANAGE

    ADMIN --> READ
    ADMIN --> CART_MANAGE
    ADMIN --> ORDER_CREATE
    ADMIN --> ORDER_MANAGE
    ADMIN --> PRODUCT_MANAGE
    ADMIN --> USER_MANAGE

    SUPERUSER --> READ
    SUPERUSER --> CART_MANAGE
    SUPERUSER --> ORDER_CREATE
    SUPERUSER --> ORDER_MANAGE
    SUPERUSER --> PRODUCT_MANAGE
    SUPERUSER --> USER_MANAGE
    SUPERUSER --> SYSTEM_ADMIN
```

## 🚀 Deployment Architecture

### Container Architecture

```mermaid
graph TB
    subgraph "Load Balancer"
        LB[Nginx Load Balancer]
    end

    subgraph "Application Tier"
        WEB1[Django Web Server 1]
        WEB2[Django Web Server 2]
        WEB3[Django Web Server 3]
    end

    subgraph "Worker Tier"
        WORKER1[Celery Worker 1]
        WORKER2[Celery Worker 2]
        BEAT[Celery Beat Scheduler]
    end

    subgraph "Data Tier"
        DB_PRIMARY[(PostgreSQL Primary)]
        DB_REPLICA[(PostgreSQL Replica)]
        REDIS_MAIN[(Redis Main)]
        REDIS_CACHE[(Redis Cache)]
    end

    subgraph "Storage Tier"
        S3_MEDIA[(S3 Media)]
        S3_STATIC[(S3 Static)]
        S3_BACKUP[(S3 Backups)]
    end

    LB --> WEB1
    LB --> WEB2
    LB --> WEB3

    WEB1 --> DB_PRIMARY
    WEB2 --> DB_PRIMARY
    WEB3 --> DB_PRIMARY

    WEB1 --> DB_REPLICA
    WEB2 --> DB_REPLICA
    WEB3 --> DB_REPLICA

    WEB1 --> REDIS_MAIN
    WEB2 --> REDIS_MAIN
    WEB3 --> REDIS_MAIN

    WEB1 --> REDIS_CACHE
    WEB2 --> REDIS_CACHE
    WEB3 --> REDIS_CACHE

    WORKER1 --> DB_PRIMARY
    WORKER2 --> DB_PRIMARY
    BEAT --> DB_PRIMARY

    WORKER1 --> REDIS_MAIN
    WORKER2 --> REDIS_MAIN
    BEAT --> REDIS_MAIN

    WEB1 --> S3_MEDIA
    WEB2 --> S3_MEDIA
    WEB3 --> S3_MEDIA

    WEB1 --> S3_STATIC
    WEB2 --> S3_STATIC
    WEB3 --> S3_STATIC

    DB_PRIMARY --> S3_BACKUP
```

### Deployment Environments

```mermaid
graph LR
    subgraph "Development"
        DEV_LOCAL[Local Development]
        DEV_DOCKER[Docker Compose]
    end

    subgraph "Staging"
        STAGING_K8S[Kubernetes Staging]
        STAGING_DB[(Staging DB)]
    end

    subgraph "Production"
        PROD_K8S[Kubernetes Production]
        PROD_DB[(Production DB)]
        PROD_CDN[CDN]
    end

    DEV_LOCAL --> DEV_DOCKER
    DEV_DOCKER --> STAGING_K8S
    STAGING_K8S --> STAGING_DB

    STAGING_K8S --> PROD_K8S
    PROD_K8S --> PROD_DB
    PROD_K8S --> PROD_CDN
```

## 📊 Monitoring & Observability

### Monitoring Stack

```mermaid
graph TB
    subgraph "Application Monitoring"
        DJANGO_LOGS[Django Logs]
        CELERY_LOGS[Celery Logs]
        NGINX_LOGS[Nginx Logs]
    end

    subgraph "Infrastructure Monitoring"
        SYSTEM_METRICS[System Metrics]
        DB_METRICS[Database Metrics]
        REDIS_METRICS[Redis Metrics]
    end

    subgraph "Business Monitoring"
        ORDER_METRICS[Order Metrics]
        REVENUE_METRICS[Revenue Metrics]
        USER_METRICS[User Metrics]
    end

    subgraph "Monitoring Tools"
        PROMETHEUS[Prometheus]
        GRAFANA[Grafana]
        ALERTMANAGER[AlertManager]
    end

    DJANGO_LOGS --> PROMETHEUS
    CELERY_LOGS --> PROMETHEUS
    NGINX_LOGS --> PROMETHEUS

    SYSTEM_METRICS --> PROMETHEUS
    DB_METRICS --> PROMETHEUS
    REDIS_METRICS --> PROMETHEUS

    ORDER_METRICS --> PROMETHEUS
    REVENUE_METRICS --> PROMETHEUS
    USER_METRICS --> PROMETHEUS

    PROMETHEUS --> GRAFANA
    PROMETHEUS --> ALERTMANAGER
```

## 🧱 Service Layer Pattern

Controllers are kept thin. Domain logic lives in dedicated service classes that sit between the HTTP controller and the Django ORM.

### Key Service Classes

| Service | Module | Responsibility |
|---|---|---|
| `OrderService` | `orders/services.py` | Create orders, apply discounts, update status |
| `CartService` | `cart/services.py` | Add/remove items, recalculate totals, merge carts |
| `CouponService` | `coupons/services.py` | Validate and redeem promo codes |
| `GiftCardService` | `gift_cards/services.py` | Issue, redeem, and track gift card balances |
| `SubscriptionService` | `subscriptions/services.py` | Create and manage Stripe Subscription lifecycle |
| `WebhookService` | `outbound_webhooks/services.py` | Dispatch events and manage delivery retries |

### Service Layer Flow

```mermaid
graph LR
    subgraph "HTTP Layer"
        CTRL[Controller]
    end

    subgraph "Service Layer"
        ORDER_SVC[OrderService]
        CART_SVC[CartService]
        COUPON_SVC[CouponService]
        GIFT_SVC[GiftCardService]
        SUB_SVC[SubscriptionService]
        WH_SVC[WebhookService]
    end

    subgraph "Data Layer"
        ORM[Django ORM / Models]
        CELERY[Celery Tasks]
        STRIPE[Stripe API]
    end

    CTRL --> ORDER_SVC
    CTRL --> CART_SVC
    ORDER_SVC --> COUPON_SVC
    ORDER_SVC --> GIFT_SVC
    ORDER_SVC --> WH_SVC
    SUB_SVC --> STRIPE

    ORDER_SVC --> ORM
    CART_SVC --> ORM
    WH_SVC --> CELERY
```

### Controller Decorator Pattern

Controllers use a composable decorator stack for cross-cutting concerns:

```python
@api_controller("/orders", tags=["Orders"])
class OrderController:
    @http_post("", response={201: OrderSchema})
    @handle_exceptions()        # structured error responses
    @log_api_call()             # request/response logging
    @require_authentication()   # JWT guard
    def create_order(self, request, payload: CreateOrderSchema):
        return 201, OrderService.create(request.user, payload)
```

Available decorators (defined in `api/utils/`):

- `@handle_exceptions()` — catches exceptions and returns structured HTTP errors
- `@log_api_call()` — logs request metadata and response status
- `@cached_response()` — Redis cache with configurable TTL and namespace
- `@paginate_response()` — standardised paginated list responses
- `@require_authentication()` — enforces valid JWT
- `@require_admin()` — restricts to staff/superuser roles

## ⚙️ Background Task Architecture

Long-running and side-effect work is offloaded to Celery workers via Redis as the broker.

### Task Categories

```mermaid
graph TB
    subgraph "Trigger Sources"
        API_CALL[API Request]
        BEAT[Celery Beat Schedule]
        WEBHOOK_IN[Inbound Stripe Webhook]
    end

    subgraph "Task Queues"
        DEFAULT[default queue]
        HIGH[high-priority queue]
        DLQ[dead-letter queue]
    end

    subgraph "Task Types"
        EMAIL[send_order_confirmation]
        INVENTORY[update_inventory_levels]
        WEBHOOK_OUT[deliver_outbound_webhook]
        ANALYTICS_EVT[record_analytics_event]
        SUB_RENEWAL[process_subscription_renewal]
        RETRY[retry_failed_webhook]
    end

    subgraph "Outcomes"
        SUCCESS[Task Success → ack]
        FAILURE[Max Retries Exceeded → DLQ]
        ALERT[DLQ Monitor → Alert]
    end

    API_CALL --> DEFAULT
    BEAT --> DEFAULT
    WEBHOOK_IN --> HIGH

    DEFAULT --> EMAIL
    DEFAULT --> INVENTORY
    DEFAULT --> WEBHOOK_OUT
    DEFAULT --> ANALYTICS_EVT
    HIGH --> SUB_RENEWAL
    DLQ --> RETRY

    EMAIL --> SUCCESS
    WEBHOOK_OUT --> SUCCESS
    WEBHOOK_OUT --> FAILURE
    FAILURE --> DLQ
    DLQ --> ALERT
```

### Dead-Letter Queue (DLQ) Pattern

Tasks that exceed their retry budget are routed to the `dead-letter` queue rather than silently dropped. A separate Celery Beat job polls the DLQ, emits a structured log entry (picked up by the OpenTelemetry collector), and optionally requeues after manual inspection.

```python
# Outbound webhook delivery with DLQ fallback
@shared_task(
    bind=True,
    max_retries=5,
    default_retry_delay=60,
    queue="default",
)
def deliver_outbound_webhook(self, webhook_id: str) -> None:
    try:
        WebhookService.deliver(webhook_id)
    except Exception as exc:
        if self.request.retries >= self.max_retries:
            deliver_outbound_webhook.apply_async(
                args=[webhook_id], queue="dead-letter"
            )
            return
        raise self.retry(exc=exc)
```

### Celery Beat Scheduled Tasks

| Task | Schedule | Purpose |
|---|---|---|
| `process_subscription_renewals` | Every hour | Trigger due subscription charges |
| `expire_gift_cards` | Daily | Mark expired gift cards inactive |
| `flush_analytics_buffer` | Every 5 min | Write buffered events to DB |
| `poll_dlq` | Every 15 min | Alert on dead-letter accumulation |

This architecture documentation provides a comprehensive overview of the Django Ecommerce API system design, ensuring scalability, maintainability, and performance for a modern e-commerce platform.
