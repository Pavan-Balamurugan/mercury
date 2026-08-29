# Mercury — Distributed E-Commerce Platform

A microservices-based e-commerce backend built to demonstrate event-driven architecture, service decomposition, and distributed system design — built as a portfolio/interview project (HPE, Amazon).

## Architecture

```
Mercury
├── User Service        (FastAPI)  — registration, login, JWT auth
├── Product Service      (FastAPI)  — product CRUD, search, Redis cache
├── Inventory Service    (FastAPI)  — stock reserve/release, conflict detection
├── Order Service        (FastAPI)  — order state machine, Kafka producer/consumer
├── Payment Service      (FastAPI)  — simulated payment, Kafka producer/consumer
│
├── PostgreSQL           — single shared schema (no db-per-service split yet)
├── Redis                — product cache only
├── Kafka + Zookeeper    — async event bus between Order and Payment services
└── Docker Compose       — local multi-service orchestration
```

## Order Placement Flow

```
Customer -> POST /orders (Order Service)
Order Service -> creates Order [PENDING]
Order Service -> calls Inventory Service synchronously (reserve stock)
  stock available?  YES -> reserve, continue
                     NO  -> Order [FAILED], stop (never reaches payment)
Order Service -> publishes OrderCreated -> Kafka (order-events)
Payment Service (consumer) -> consumes OrderCreated, simulates payment
Payment Service -> publishes PaymentCompleted / PaymentFailed -> Kafka (payment-events)
Order Service (consumer) -> consumes payment event
  PaymentCompleted -> Order [CONFIRMED]
  PaymentFailed    -> Order [PAYMENT_FAILED], releases reserved stock
```

Inventory reservation is synchronous because the customer needs an immediate answer on stock availability. Payment is asynchronous via Kafka because it doesn't need to block the request.

## Order State Machine

```
PENDING -> PAYMENT_PENDING -> CONFIRMED
PENDING -> FAILED                          (inventory conflict)
PAYMENT_PENDING -> PAYMENT_FAILED          (payment declined, stock released)
```

## Running Locally

```bash
docker-compose up -d
```

Services come up on:
- User Service: `localhost:8001`
- Product Service: `localhost:8002`
- Inventory Service: `localhost:8003`
- Order Service: `localhost:8004`
- Payment Service: internal only (Kafka consumer, no exposed port)

Kafka takes 15-30s to become fully ready after container start; Order/Payment services wait on Kafka's healthcheck before starting.

## Demo Script

**1. Register + login**
```bash
POST localhost:8001/auth/register  {"email": "...", "password": "..."}
POST localhost:8001/auth/login     {"email": "...", "password": "..."}
```

**2. Create a product + set stock**
```bash
POST localhost:8002/products      {"name": "...", "price": ..., "category": "..."}
PUT  localhost:8003/inventory/{product_id}   {"available_qty": 10}
```

**3. Happy path — place an order within stock**
```bash
POST localhost:8004/orders  {"user_id": "...", "items": [{"product_id": "...", "quantity": 2}]}
GET  localhost:8004/orders/{order_id}
```
Order flows PENDING -> PAYMENT_PENDING -> CONFIRMED (or PAYMENT_FAILED, ~20% simulated failure rate).

**4. Failure path — deliberately exceed stock**
```bash
POST localhost:8004/orders  {"user_id": "...", "items": [{"product_id": "...", "quantity": 999}]}
```
Order goes straight to FAILED — inventory conflict caught before payment is ever attempted, and no stock is reserved.

## Design Decisions & Scope Cuts

This is a trimmed MVP (v1.1) of a larger PRD, scoped for a demoable build alongside active interview prep:

- **API Gateway** — cut; services called directly. Gateway pattern explained verbally in interviews.
- **Cart Service** — folded into Order Service as a simple items table.
- **Notification Service** — not built.
- **Kubernetes** — Docker Compose only for local dev; K8s deployment plan described verbally.
- **Database-per-service** — single shared Postgres schema for now, not per-service split.
- **Cloud Sentinel** (observability/security platform consuming these services' logs) — a separate, parallel project, not part of this repo.

## Tech Stack

FastAPI, SQLAlchemy, PostgreSQL, Redis, Kafka (aiokafka), Docker Compose, JWT auth (python-jose + passlib/bcrypt).

