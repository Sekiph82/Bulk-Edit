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

### [SAFETY] AI Output: Preview-Only
AI output must never be applied directly to listings. Always goes through preview → user approval flow. Rationale: AI output quality varies; seller is responsible for their listing content.
