# ARCHITECTURE.md — System Architecture

## Overview

Bulk-Edit is a multi-tenant SaaS platform.

## Local Development Ports

Custom host ports used to avoid conflict with other local projects:

| Service | Host Port | Container Port | URL (local) |
|---|---|---|---|
| Frontend | 3100 | 3000 | http://localhost:3100 |
| Backend | 8100 | 8000 | http://localhost:8100 |
| PostgreSQL | 55432 | 5432 | localhost:55432 |
| Redis | 56379 | 6379 | localhost:56379 |

Docker Compose internal service communication uses container ports and service names (e.g., `postgres:5432`, `redis:6379`). Production uses standard ports (80/443) behind a reverse proxy. Each organization (seller) connects one or more Etsy shops and manages their listings through a web application. The system is split into a Next.js frontend and a FastAPI backend, backed by PostgreSQL, Redis, and S3-compatible storage.

---

## System Diagram

```
┌──────────────────────────────────────────────────────────────────┐
│                          Browser (User)                          │
└──────────────────────────────┬───────────────────────────────────┘
                               │ HTTPS
                               ▼
┌──────────────────────────────────────────────────────────────────┐
│                    Next.js 14 Frontend                           │
│                    (App Router / TypeScript)                     │
│  - Auth pages    - Listings grid    - Bulk editor               │
│  - AI tools UI   - Media library    - Billing pages             │
└──────────────────────────────┬───────────────────────────────────┘
                               │ REST API (HTTPS)
                               ▼
┌──────────────────────────────────────────────────────────────────┐
│                    FastAPI Backend                               │
│  ┌───────────┐  ┌───────────┐  ┌────────────┐  ┌────────────┐  │
│  │  Auth     │  │  Billing  │  │  Listings  │  │  AI Tools  │  │
│  │  Router   │  │  Router   │  │  Router    │  │  Router    │  │
│  └───────────┘  └───────────┘  └────────────┘  └────────────┘  │
│  ┌───────────┐  ┌───────────┐  ┌────────────┐  ┌────────────┐  │
│  │  Bulk     │  │  Media    │  │  CSV       │  │  Admin     │  │
│  │  Router   │  │  Router   │  │  Router    │  │  Router    │  │
│  └───────────┘  └───────────┘  └────────────┘  └────────────┘  │
│                                                                  │
│  Service Layer → Models → Database                               │
└──────┬───────────────────┬───────────────────────┬──────────────┘
       │                   │                       │
       ▼                   ▼                       ▼
┌─────────────┐   ┌──────────────┐       ┌───────────────┐
│ PostgreSQL  │   │   Redis      │       │  S3 / MinIO   │
│ (Primary DB)│   │ Cache/Queue  │       │  (Media)      │
└─────────────┘   └──────┬───────┘       └───────────────┘
                         │
                         ▼
                  ┌─────────────┐
                  │   Celery    │
                  │  Workers    │
                  └─────────────┘
                         │
              ┌──────────┼──────────┐
              ▼          ▼          ▼
         Etsy API   OpenAI API  Anthropic API
```

---

## Monorepo Structure

```
Bulk-Edit/
├── apps/
│   ├── frontend/          # Next.js 14
│   │   ├── app/           # App Router pages
│   │   ├── components/    # Reusable UI components
│   │   ├── hooks/         # Custom React hooks
│   │   ├── lib/           # API client, utilities
│   │   └── styles/        # Global styles
│   └── backend/           # FastAPI
│       ├── app/
│       │   ├── routers/   # Route handlers
│       │   ├── services/  # Business logic
│       │   ├── models/    # SQLAlchemy models
│       │   ├── schemas/   # Pydantic schemas
│       │   ├── auth/      # JWT, OAuth handlers
│       │   ├── etsy/      # Etsy API client
│       │   ├── bulk/      # Bulk edit engine
│       │   ├── ai/        # AI tool integrations
│       │   ├── media/     # S3 media handling
│       │   ├── billing/   # Stripe integration
│       │   ├── tasks/     # Celery task definitions
│       │   └── middleware/ # Auth, logging, rate limit
│       ├── alembic/       # Migrations
│       └── tests/         # Pytest test suite
├── packages/
│   └── shared/            # Shared TypeScript types
├── docs/
├── scripts/
├── docker-compose.yml
├── Makefile
├── .env.example
└── README.md
```

---

## Data Flow: Bulk Edit

```
1. User selects listings in grid
2. User configures bulk edit fields
3. Frontend calls POST /bulk-edit/sessions
4. Backend creates BulkEditSession with staged changes
5. Frontend calls GET /bulk-edit/sessions/{id}/preview
6. Backend returns field-level diff per listing
7. User reviews preview, adjusts if needed
8. User confirms → Frontend calls POST /bulk-edit/sessions/{id}/apply
9. Backend: snapshot all affected listings
10. Backend: check subscription gate
11. Backend: write to Etsy API (rate limited)
12. Backend: write audit log
13. Frontend: show progress and results
```

---

## Data Flow: Magic Revert

```
1. User opens Revert History
2. Frontend calls GET /snapshots (lists all backup sessions)
3. User selects snapshot to revert to
4. Frontend calls POST /snapshots/{id}/revert
5. Backend: show preview of revert changes
6. User confirms revert
7. Backend: write reverted values to Etsy API
8. Backend: log revert in audit log
```

---

## Multi-Tenancy Model

- Each user belongs to one `Organization`
- Each `Organization` has one `Subscription`
- Each `Organization` can connect multiple `EtsyShop`s
- All data is scoped by `organization_id`
- Row-level filtering enforced in all service layer queries

---

## Key Database Tables

See `docs/technical/DATABASE_SCHEMA.md` for full schema.

Core tables:
- `users`
- `organizations`
- `organization_members`
- `subscriptions`
- `etsy_shops`
- `etsy_tokens`
- `listings`
- `listing_images`
- `listing_variations`
- `bulk_edit_sessions`
- `bulk_edit_changes`
- `listing_snapshots`
- `revert_logs`
- `media_assets`
- `audit_logs`
- `scheduled_jobs`
- `csv_jobs`
