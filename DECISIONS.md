# DECISIONS.md — Architecture and Product Decisions

Format: `[DATE] [CATEGORY] Decision — Rationale`

---

## 2026-06-25

### [STACK] Frontend: Next.js 14 with App Router
Next.js 14 App Router chosen for SSR, file-based routing, server components, and strong TypeScript support. Aligns with modern React patterns. Alternative considered: Remix (rejected — smaller ecosystem).

### [STACK] Backend: FastAPI (Python 3.12)
FastAPI chosen for async-first design, automatic OpenAPI docs, Pydantic validation, and strong ecosystem for AI/ML integrations. Alternative considered: Node.js/Express (rejected — weaker AI library ecosystem).

### [STACK] Database: PostgreSQL 16
PostgreSQL chosen for JSONB support (listing metadata), full-text search, strong relational guarantees, and wide hosting support. Alternative considered: MySQL (rejected — weaker JSONB support).

### [STACK] ORM: SQLAlchemy 2.x + Alembic
SQLAlchemy 2.x async support with Alembic migrations. Industry standard for Python/PostgreSQL. No alternatives seriously considered.

### [STACK] Cache / Queue: Redis 7
Redis used for both caching and Celery broker. Single dependency serving two purposes. Alternative considered: RabbitMQ as broker (rejected — adds complexity for no gain at this scale).

### [STACK] Task Queue: Celery
Celery with Redis broker for background jobs. Mature, well-documented, integrates with FastAPI. Alternative considered: ARQ (rejected — smaller community, fewer features).

### [STACK] Auth: JWT (access + refresh)
JWT with short-lived access tokens (15 min) and rotating refresh tokens (7 days). Token blacklist in Redis. No server-side sessions to keep backend stateless.

### [STACK] Storage: S3-compatible
MinIO for local development, AWS S3 (or compatible) for production. Presigned URLs for direct client uploads. No media stored on application servers.

### [STACK] AI: OpenAI GPT-4o + Anthropic Claude
Dual-provider AI support. OpenAI GPT-4o for primary AI tools. Anthropic Claude as fallback and for specific use cases. Both require preview before apply.

### [PRODUCT] Subscription Tiers: Free, Monthly, Yearly
Three tiers: Free (limited features), Monthly Pro, Yearly Pro (discounted). No per-seat pricing at v1. Decision can be revisited after launch.

### [PRODUCT] Monorepo Structure
All code in single repo: `apps/frontend`, `apps/backend`, `packages/shared`. Simplifies CI/CD and type sharing at the cost of slightly more complex repo management.

### [SAFETY] External Write Protocol: 6-Step
All Etsy writes require: preview → user confirmation → snapshot → permission check → subscription gate → audit log. Non-negotiable. Rationale: Etsy write mistakes can cause seller revenue loss and are hard to reverse without our Magic Revert system.

---

## 2026-06-25 (Sprint 1)

### [BACKEND] Async SQLAlchemy engine pool config
Set `pool_size=10`, `max_overflow=20`, `pool_pre_ping=True`. Sufficient for initial load. Can tune in Sprint 18 based on observed connection patterns.

### [BACKEND] Health endpoints at /api/v1/health (not /health)
Chose `/api/v1/health` prefix to stay consistent with API versioning. All future endpoints under `/api/v1/`.

### [BACKEND] pydantic-settings model_config over inner Config class
Used Pydantic v2 `model_config` dict syntax instead of deprecated inner `Config` class. Avoids deprecation warnings with Pydantic 2.x.

### [INFRA] Custom local host ports to avoid conflict with other projects
Frontend host port: 3100 (container: 3000, mapping 3100:3000)
Backend host port: 8100 (container: 8000, mapping 8100:8000)
PostgreSQL host port: 55432 (container: 5432, mapping 55432:5432)
Redis host port: 56379 (container: 6379, mapping 56379:6379)
Rationale: avoids collision with another active local project using ports 3000, 8000, 5432, 6379. Production uses standard ports (80/443). Docker Compose internal traffic uses standard container ports (service-to-service).

### [BACKEND] BACKEND_CORS_ORIGINS stored as str, not List[str]
pydantic-settings v2 pre-parses `List[str]` fields as JSON before field validators run. Storing as `str` avoids this. `settings.get_cors_origins()` method handles parsing (plain string, comma-separated, or JSON array). `main.py` calls `settings.get_cors_origins()` when configuring CORS middleware.

### [DEPS] anyio 4.6.2 yanked warning
`anyio==4.6.2` in requirements-dev.txt is yanked on PyPI (mistagged 4.5.2 code). Still functional. Will update when `anyio>=4.7.0` is stable and compatible with pytest-asyncio 0.24.x.

### [FRONTEND] No shadcn/ui in Sprint 1
shadcn/ui setup deferred to Sprint 2 when auth pages will benefit from its form components. Sprint 1 uses raw Tailwind only.

### [SAFETY] AI Output: Preview-Only
AI output must never be applied directly to listings. Always goes through preview → user approval flow. Rationale: AI output quality varies; seller is responsible for their listing content.
