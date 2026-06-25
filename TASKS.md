# TASKS.md — Phased Roadmap

Legend: `[ ]` todo · `[~]` in progress · `[x]` done · `[!]` blocked

---

## Sprint 0: Project Memory and Operating System

**Status:** `[x] COMPLETE`

- [x] Create CLAUDE.md
- [x] Create TASKS.md
- [x] Create SKILLS.md
- [x] Create PROJECT_STATUS.md
- [x] Create HANDOFF.md
- [x] Create DECISIONS.md
- [x] Create ARCHITECTURE.md
- [x] Create LIMIT_PROTOCOL.md
- [x] Create SECURITY.md
- [x] Create CHANGELOG_AI.md
- [x] Create ROADMAP.md
- [x] Create README.md
- [x] Create .env.example
- [x] Create .claude/commands/continue.md
- [x] Create .claude/commands/checkpoint.md
- [x] Create .claude/commands/finish-session.md
- [x] Create .claude/commands/plan-next.md
- [x] Create .claude/commands/skill-select.md
- [x] Create .claude/commands/audit.md
- [x] Create docs/product/PRODUCT_REQUIREMENTS.md
- [x] Create docs/product/FEATURES.md
- [x] Create docs/product/PRICING.md
- [x] Create docs/product/USER_FLOWS.md
- [x] Create docs/technical/DATABASE_SCHEMA.md
- [x] Create docs/technical/API_SPEC.md
- [x] Create docs/technical/ETSY_INTEGRATION.md
- [x] Create docs/technical/STRIPE_BILLING.md
- [x] Create docs/technical/BULK_ENGINE.md
- [x] Create docs/technical/AI_TOOLS.md
- [x] Create docs/technical/MEDIA_LIBRARY.md
- [x] Create docs/technical/SECURITY_MODEL.md
- [x] Create docs/operations/DEPLOYMENT.md
- [x] Create docs/operations/TESTING.md
- [x] Create docs/operations/RELEASE_CHECKLIST.md
- [x] Commit and push to GitHub

---

## Sprint 1: Monorepo Skeleton

**Status:** `[x] COMPLETE`

- [x] Initialize monorepo structure: `apps/frontend`, `apps/backend`, `packages/`
- [x] Scaffold Next.js 14 frontend (TypeScript, App Router, Tailwind CSS)
- [x] Scaffold FastAPI backend (Python 3.12, uvicorn)
- [x] Configure PostgreSQL with Docker Compose (host port 55432)
- [x] Configure Redis with Docker Compose (host port 56379)
- [x] Set up Alembic migrations
- [x] Set up SQLAlchemy base models
- [x] Add health check endpoints: `GET /api/v1/health`, `GET /api/v1/health/db`, `GET /api/v1/health/redis`
- [x] Add root `docker-compose.yml` with custom host ports (3100, 8100, 55432, 56379)
- [x] Add root `Makefile` with common commands
- [x] Add root `.gitignore`
- [x] Align `.env.example` with all services and custom ports
- [x] Update README with local setup instructions and correct ports
- [x] Add landing page `/` and dashboard placeholder `/dashboard`
- [x] Fix BACKEND_CORS_ORIGINS to accept plain string (pydantic-settings v2 compatibility)
- [x] CORS origins validator: handles plain string, comma-separated, JSON array
- [x] Run pytest — 4/4 tests pass, zero warnings
- [x] Commit and push

---

## Sprint 2: Auth + Organization

**Status:** `[x] COMPLETE`

- [x] Design User, Organization, OrganizationMember models
- [x] Implement user registration endpoint (POST /api/v1/auth/register)
- [x] Implement user login endpoint (POST /api/v1/auth/login — JWT access + refresh)
- [x] Implement token refresh endpoint (POST /api/v1/auth/refresh — rotation)
- [x] Implement logout (POST /api/v1/auth/logout — revoke refresh token in DB)
- [x] Implement GET /api/v1/auth/me — returns user + memberships
- [x] Build frontend auth pages: /register, /login (Tailwind forms)
- [x] Update dashboard with auth state + logout button
- [x] Add auth middleware to FastAPI (HTTPBearer + get_current_user dep)
- [x] RefreshToken model with SHA-256 token_hash
- [x] SQLite + aiosqlite test fixtures (override get_db per test)
- [x] Write auth tests — 14/14 PASSED
- [x] Commit and push

---

## Sprint 3: Stripe Billing and Feature Gates

**Status:** `[ ] TODO`

- [ ] Design Subscription, Plan, BillingEvent models
- [ ] Create Stripe products and prices (Free, Monthly, Yearly)
- [ ] Implement Stripe checkout session endpoint
- [ ] Implement Stripe webhook handler
- [ ] Implement subscription status sync
- [ ] Implement feature gate middleware (plan-based access control)
- [ ] Build frontend pricing page
- [ ] Build frontend billing management page
- [ ] Add plan upgrade/downgrade flow
- [ ] Write billing unit tests
- [ ] Commit and push

---

## Sprint 4: Etsy OAuth

**Status:** `[ ] TODO`

- [ ] Register Etsy app in developer portal
- [ ] Implement Etsy OAuth2 PKCE flow
- [ ] Store encrypted Etsy tokens per shop
- [ ] Implement token refresh logic
- [ ] Design EtsyShop, EtsyToken models
- [ ] Build frontend Etsy connect flow
- [ ] Add shop disconnect endpoint
- [ ] Write Etsy auth tests
- [ ] Commit and push

---

## Sprint 5: Listing Sync

**Status:** `[ ] TODO`

- [ ] Design Listing, ListingImage, ListingVariation models
- [ ] Implement Etsy listing fetch (paginated)
- [ ] Implement listing snapshot storage
- [ ] Implement sync status tracking
- [ ] Build Celery sync task
- [ ] Add webhook for Etsy listing updates (if available)
- [ ] Build frontend sync status UI
- [ ] Write sync tests
- [ ] Commit and push

---

## Sprint 6: Listings Grid

**Status:** `[ ] TODO`

- [ ] Build paginated, filterable listings grid (frontend)
- [ ] Add search, filter by status/section/tag
- [ ] Add multi-select checkboxes
- [ ] Add listing thumbnail previews
- [ ] Add sort controls
- [ ] Build listing detail sidebar
- [ ] Commit and push

---

## Sprint 7: Bulk Edit Preview Engine

**Status:** `[ ] TODO`

- [ ] Design BulkEditSession, BulkEditChange models
- [ ] Implement bulk edit session creation API
- [ ] Implement field-level change diffing
- [ ] Build preview modal showing before/after per listing
- [ ] Add per-field override in preview
- [ ] Add bulk discard / confirm UI
- [ ] Write bulk engine unit tests
- [ ] Commit and push

---

## Sprint 8: Etsy Write + Backup

**Status:** `[ ] TODO`

- [ ] Implement listing snapshot backup before write
- [ ] Implement Etsy listing update API calls
- [ ] Add rate limiting / throttling for Etsy API
- [ ] Add per-write audit log entries
- [ ] Add subscription gate checks before writes
- [ ] Add write progress indicator (frontend)
- [ ] Write safe-write integration tests
- [ ] Commit and push

---

## Sprint 9: Magic Revert

**Status:** `[ ] TODO`

- [ ] Design ListingSnapshot, RevertLog models
- [ ] Implement revert session creation
- [ ] Implement selective revert (per listing, per field)
- [ ] Implement full bulk revert
- [ ] Build revert history UI
- [ ] Add revert confirmation modal
- [ ] Write revert tests
- [ ] Commit and push

---

## Sprint 10: Media Library

**Status:** `[ ] TODO`

- [ ] Design MediaAsset model
- [ ] Implement S3 upload endpoint (presigned URLs)
- [ ] Implement media asset listing and search
- [ ] Implement media delete
- [ ] Build frontend media library grid
- [ ] Add drag-and-drop upload
- [ ] Write media tests
- [ ] Commit and push

---

## Sprint 11: Photo / Video Bulk Editor

**Status:** `[ ] TODO`

- [ ] Implement bulk photo replacement
- [ ] Implement bulk photo reorder
- [ ] Implement bulk video assignment
- [ ] Add alt text bulk editor
- [ ] Build photo/video editor UI panel
- [ ] Write photo/video tests
- [ ] Commit and push

---

## Sprint 12: Variation Editor

**Status:** `[ ] TODO`

- [ ] Implement bulk variation price edit
- [ ] Implement bulk variation quantity edit
- [ ] Implement bulk variation SKU edit
- [ ] Build variation editor UI
- [ ] Write variation tests
- [ ] Commit and push

---

## Sprint 13: AI Tools

**Status:** `[ ] TODO`

- [ ] Implement AI title optimizer endpoint
- [ ] Implement AI description writer endpoint
- [ ] Implement AI tag generator endpoint
- [ ] Implement AI alt text generator endpoint
- [ ] Implement AI SEO scorer endpoint
- [ ] Implement AI category suggester endpoint
- [ ] Build AI tools panel UI (preview before apply)
- [ ] Add AI output approval flow
- [ ] Write AI tool tests
- [ ] Commit and push

---

## Sprint 14: CSV Import / Export

**Status:** `[ ] TODO`

- [ ] Design CSVJob model
- [ ] Implement CSV export of listings
- [ ] Implement CSV import with validation
- [ ] Build import preview (diff before apply)
- [ ] Build frontend CSV import/export UI
- [ ] Write CSV tests
- [ ] Commit and push

---

## Sprint 15: Dynamic Pricing

**Status:** `[ ] TODO`

- [ ] Design PricingRule model
- [ ] Implement rule-based price calculation engine
- [ ] Implement bulk price preview with rules applied
- [ ] Build pricing rule editor UI
- [ ] Write dynamic pricing tests
- [ ] Commit and push

---

## Sprint 16: Scheduled Jobs

**Status:** `[ ] TODO`

- [ ] Design ScheduledJob model
- [ ] Implement job scheduler (Celery Beat)
- [ ] Implement scheduled listing sync
- [ ] Implement scheduled bulk edit
- [ ] Build job scheduler UI
- [ ] Write scheduler tests
- [ ] Commit and push

---

## Sprint 17: Admin Panel

**Status:** `[ ] TODO`

- [ ] Build admin user management page
- [ ] Build admin subscription management page
- [ ] Build admin audit log viewer
- [ ] Build admin system health page
- [ ] Add admin-only API routes with role gate
- [ ] Write admin tests
- [ ] Commit and push

---

## Sprint 18: Tests, Deployment, Security Hardening, Polish

**Status:** `[ ] TODO`

- [ ] Achieve >80% backend test coverage
- [ ] Achieve >70% frontend test coverage
- [ ] Run OWASP security audit
- [ ] Fix all critical/high findings
- [ ] Configure GitHub Actions CI/CD pipeline
- [ ] Write production Docker Compose / Kubernetes configs
- [ ] Configure SSL, rate limiting, CORS, CSP headers
- [ ] Performance audit and optimization
- [ ] Accessibility audit (WCAG 2.1 AA)
- [ ] Final QA pass
- [ ] Write release checklist
- [ ] Tag v1.0.0
- [ ] Commit and push

---

## Backlog / Future

- [ ] Shopify integration
- [ ] Multi-language support
- [ ] Mobile app
- [ ] Affiliate program
- [ ] Public API for integrations
