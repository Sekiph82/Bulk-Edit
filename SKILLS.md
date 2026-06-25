# SKILLS.md — Skill Registry

Each skill defines a focused responsibility domain. Select skills before starting any task.

---

## 01 documentation-handoff

### Use when
Starting or ending a session. Creating or updating memory files, handoff notes, decision logs, changelogs, or roadmap files.

### Responsibilities
- Write and maintain CLAUDE.md, TASKS.md, HANDOFF.md, DECISIONS.md, CHANGELOG_AI.md, PROJECT_STATUS.md
- Write session summaries
- Document blockers and next steps

### Rules
- Always read all 7 session-start files before doing anything else
- Always update all 5 session-end files before stopping
- Never leave HANDOFF.md without an exact next prompt

### Usually touches
`CLAUDE.md`, `TASKS.md`, `SKILLS.md`, `PROJECT_STATUS.md`, `HANDOFF.md`, `DECISIONS.md`, `CHANGELOG_AI.md`, `ROADMAP.md`

### Must update
`TASKS.md`, `PROJECT_STATUS.md`, `HANDOFF.md`, `CHANGELOG_AI.md`

### Required tests
None. Verify all files exist and are non-empty.

---

## 02 limit-recovery

### Use when
Approaching context limits, hitting token limits, or resuming after an interrupted session.

### Responsibilities
- Run checkpoint protocol
- Save all in-progress state
- Write exact resume instructions in HANDOFF.md
- Avoid starting new work near limits

### Rules
- Stop new work immediately when limit is near
- Update HANDOFF.md with exact file, line, and next action
- Never leave work in a broken state

### Usually touches
`HANDOFF.md`, `PROJECT_STATUS.md`, `TASKS.md`, `CHANGELOG_AI.md`

### Must update
`HANDOFF.md`, `TASKS.md`, `PROJECT_STATUS.md`, `CHANGELOG_AI.md`

### Required tests
None.

---

## 03 product-architect

### Use when
Defining product requirements, user flows, feature specs, pricing tiers, or making product-level decisions.

### Responsibilities
- Write and maintain product documentation
- Define feature scope per subscription tier
- Design user flows
- Make product trade-off decisions

### Rules
- All feature decisions must be documented in DECISIONS.md
- Paid features must be clearly tagged with required plan
- User flows must cover happy path and error states

### Usually touches
`docs/product/PRODUCT_REQUIREMENTS.md`, `docs/product/FEATURES.md`, `docs/product/PRICING.md`, `docs/product/USER_FLOWS.md`, `DECISIONS.md`

### Must update
`DECISIONS.md`, `TASKS.md`

### Required tests
None. Peer review of specs recommended.

---

## 04 system-architect

### Use when
Designing system architecture, database schemas, API contracts, integration patterns, or making technical stack decisions.

### Responsibilities
- Maintain ARCHITECTURE.md
- Design data models
- Define API surface
- Define integration patterns for Etsy, Stripe, S3, Redis

### Rules
- All architectural decisions must be in DECISIONS.md
- No schema changes without Alembic migration plan
- API contracts must be documented before implementation

### Usually touches
`ARCHITECTURE.md`, `docs/technical/DATABASE_SCHEMA.md`, `docs/technical/API_SPEC.md`, `DECISIONS.md`

### Must update
`ARCHITECTURE.md`, `DECISIONS.md`

### Required tests
None directly. Validate schemas with migrations before merge.

---

## 05 repo-setup

### Use when
Initializing the monorepo, setting up Docker Compose, configuring CI/CD, writing Makefiles, or scaffolding project structure.

### Responsibilities
- Create and maintain monorepo layout
- Configure Docker Compose for all services
- Set up GitHub Actions workflows
- Write Makefile commands
- Align .env.example with all services

### Rules
- Never commit real secrets
- Docker Compose must start all services with a single command
- .env.example must stay in sync with all service configs

### Usually touches
`docker-compose.yml`, `Makefile`, `.env.example`, `.github/workflows/`, `apps/`, `packages/`

### Must update
`README.md`, `.env.example`, `TASKS.md`

### Required tests
`docker compose up` must succeed. All health endpoints must return 200.

---

## 06 database-modeling

### Use when
Designing or modifying PostgreSQL schemas, writing Alembic migrations, or updating SQLAlchemy models.

### Responsibilities
- Design normalized, indexed database schemas
- Write Alembic migration files
- Define SQLAlchemy ORM models
- Maintain DATABASE_SCHEMA.md

### Rules
- Every schema change needs an Alembic migration
- No raw SQL in application code — use ORM
- All foreign keys must have ON DELETE behavior defined
- Index all frequently queried columns

### Usually touches
`apps/backend/alembic/`, `apps/backend/app/models/`, `docs/technical/DATABASE_SCHEMA.md`

### Must update
`docs/technical/DATABASE_SCHEMA.md`, `DECISIONS.md` (if schema decision)

### Required tests
Migration must apply and rollback cleanly. Model unit tests required.

---

## 07 backend-api

### Use when
Writing FastAPI route handlers, service layer functions, request/response schemas, or background task logic.

### Responsibilities
- Implement REST API endpoints
- Write Pydantic schemas
- Write service layer logic
- Handle errors consistently
- Add logging and observability hooks

### Rules
- All endpoints must have Pydantic request/response schemas
- No business logic in route handlers — use service layer
- All errors must return structured JSON responses
- All paid features must check subscription gate

### Usually touches
`apps/backend/app/routers/`, `apps/backend/app/services/`, `apps/backend/app/schemas/`, `apps/backend/app/models/`

### Must update
`docs/technical/API_SPEC.md`, `TASKS.md`

### Required tests
Unit tests for service layer. Integration tests for endpoints.

---

## 08 frontend-ui

### Use when
Building Next.js pages, components, hooks, or frontend state management.

### Responsibilities
- Build React components with TypeScript
- Implement pages using App Router
- Write data fetching hooks
- Implement form handling and validation
- Build responsive layouts with Tailwind CSS

### Rules
- No hardcoded API URLs — use environment variables
- All pages must have loading and error states
- All forms must have client-side and server-side validation
- All destructive actions must have confirmation dialogs

### Usually touches
`apps/frontend/app/`, `apps/frontend/components/`, `apps/frontend/hooks/`, `apps/frontend/lib/`

### Must update
`TASKS.md`

### Required tests
Component unit tests. E2E tests for critical flows.

---

## 09 auth-security

### Use when
Implementing authentication, authorization, JWT handling, session management, or RBAC.

### Responsibilities
- Implement JWT access and refresh token flow
- Implement token blacklisting via Redis
- Implement role-based access control
- Implement email verification and password reset
- Protect API routes with auth middleware

### Rules
- Tokens must have short expiry (access: 15min, refresh: 7 days)
- Refresh tokens must be rotated on use
- Passwords must be hashed with bcrypt (min cost 12)
- Never log tokens or passwords
- HTTPS only in production

### Usually touches
`apps/backend/app/auth/`, `apps/backend/app/middleware/`, `apps/frontend/app/(auth)/`, `docs/technical/SECURITY_MODEL.md`

### Must update
`docs/technical/SECURITY_MODEL.md`, `SECURITY.md`

### Required tests
Auth unit tests. Token expiry tests. RBAC permission tests.

---

## 10 billing-stripe

### Use when
Implementing Stripe checkout, webhooks, subscription management, or plan-based feature gating.

### Responsibilities
- Integrate Stripe Checkout and Customer Portal
- Handle Stripe webhooks securely
- Sync subscription status to database
- Implement feature gate middleware
- Build pricing and billing UI

### Rules
- Always verify Stripe webhook signatures
- Never store raw card data
- Subscription status must sync on every webhook event
- Feature gates must check database subscription status, not session cache

### Usually touches
`apps/backend/app/billing/`, `apps/backend/app/routers/billing.py`, `apps/frontend/app/(billing)/`, `docs/technical/STRIPE_BILLING.md`

### Must update
`docs/technical/STRIPE_BILLING.md`, `DECISIONS.md` (pricing decisions)

### Required tests
Webhook handler tests with mock Stripe events. Feature gate unit tests.

---

## 11 etsy-integration

### Use when
Implementing Etsy OAuth, listing fetch, shop sync, or any read from the Etsy API.

### Responsibilities
- Implement Etsy OAuth2 PKCE flow
- Store and refresh Etsy API tokens
- Fetch and paginate Etsy listings
- Map Etsy API responses to internal models
- Handle Etsy API rate limits

### Rules
- Always use PKCE for Etsy OAuth
- Never store plaintext Etsy tokens — encrypt at rest
- Respect Etsy API rate limits (10 req/sec default)
- Log all Etsy API errors

### Usually touches
`apps/backend/app/etsy/`, `apps/backend/app/models/etsy_*.py`, `docs/technical/ETSY_INTEGRATION.md`

### Must update
`docs/technical/ETSY_INTEGRATION.md`

### Required tests
OAuth flow tests with mock. Listing sync tests with fixture data.

---

## 12 safe-external-write

### Use when
Writing any data back to the Etsy API (listing updates, photo uploads, etc.).

### Responsibilities
- Enforce the 6-step external write safety protocol
- Generate change preview before write
- Create snapshot backup before write
- Check subscription feature gate
- Write to audit log
- Execute write and confirm

### Rules
- NEVER skip any step in the write protocol
- NEVER write without user confirmation
- NEVER write without a snapshot backup
- NEVER write without audit log entry
- If any step fails, abort entire write batch

### Usually touches
`apps/backend/app/etsy/writer.py`, `apps/backend/app/services/snapshot.py`, `apps/backend/app/services/audit.py`

### Must update
Audit log (always), `TASKS.md`

### Required tests
Write protocol integration tests. Rollback tests. Gate enforcement tests.

---

## 13 bulk-edit-engine

### Use when
Implementing bulk edit sessions, change diffing, field-level edits, or preview generation.

### Responsibilities
- Design and implement BulkEditSession model
- Implement field-level change accumulation
- Generate before/after diffs per listing
- Apply changes to Etsy via safe-external-write
- Support partial apply (selected listings only)

### Rules
- All bulk edits must go through preview before apply
- Changes must be diffed at field level
- Never apply without user confirmation
- Always use safe-external-write for Etsy writes

### Usually touches
`apps/backend/app/bulk/`, `apps/backend/app/models/bulk_*.py`, `docs/technical/BULK_ENGINE.md`

### Must update
`docs/technical/BULK_ENGINE.md`, `TASKS.md`

### Required tests
Diff engine unit tests. Session state machine tests. Preview accuracy tests.

---

## 14 background-jobs

### Use when
Implementing Celery tasks, scheduled sync, import/export jobs, or any async processing.

### Responsibilities
- Write Celery task definitions
- Configure Celery Beat for scheduled tasks
- Implement job status tracking
- Handle task retries and failures
- Build job status UI

### Rules
- All long-running operations must be background tasks
- Tasks must be idempotent where possible
- Failures must be logged and surfaced to UI
- Never block the HTTP request cycle with long operations

### Usually touches
`apps/backend/app/tasks/`, `apps/backend/celery_worker.py`, `apps/backend/celery_beat.py`

### Must update
`TASKS.md`

### Required tests
Task unit tests. Retry behavior tests. Idempotency tests.

---

## 15 media-processing

### Use when
Implementing media upload, S3 storage, image/video processing, or the media library.

### Responsibilities
- Generate S3 presigned upload URLs
- Store media asset metadata in database
- Implement media search and filtering
- Handle image resizing and thumbnail generation
- Implement video upload support

### Rules
- Never store media in the application server filesystem
- Always use presigned URLs for uploads
- Validate file types and sizes before accepting uploads
- Store only metadata in database, binary in S3

### Usually touches
`apps/backend/app/media/`, `apps/backend/app/models/media.py`, `docs/technical/MEDIA_LIBRARY.md`

### Must update
`docs/technical/MEDIA_LIBRARY.md`, `TASKS.md`

### Required tests
Upload flow tests. Presigned URL tests. Media metadata tests.

---

## 16 ai-tools

### Use when
Implementing AI-powered title, description, tag, alt text, SEO, or category tools.

### Responsibilities
- Integrate OpenAI GPT-4o and Anthropic Claude APIs
- Build prompt templates per tool type
- Return structured AI output for preview
- Never apply AI output without user approval
- Track AI token usage per organization

### Rules
- AI output must ALWAYS go to preview first
- Never auto-apply AI output to listings
- Log all AI requests and responses (without PII)
- Rate limit AI endpoints per subscription plan

### Usually touches
`apps/backend/app/ai/`, `apps/backend/app/routers/ai.py`, `docs/technical/AI_TOOLS.md`

### Must update
`docs/technical/AI_TOOLS.md`, `TASKS.md`

### Required tests
Prompt template unit tests. Output schema validation tests. Approval gate tests.

---

## 17 csv-import-export

### Use when
Implementing CSV export of listings, CSV import with validation, or import preview.

### Responsibilities
- Define CSV column schema matching listing fields
- Implement CSV export with all listing fields
- Implement CSV import with row-level validation
- Generate import preview diff before apply
- Handle encoding and large file streaming

### Rules
- CSV imports must show preview before apply
- Validate every row before accepting import
- Export must include all editable fields
- Never apply CSV import without user confirmation

### Usually touches
`apps/backend/app/csv/`, `apps/backend/app/tasks/csv_tasks.py`

### Must update
`TASKS.md`

### Required tests
Export round-trip tests. Import validation tests. Large file streaming tests.

---

## 18 scheduling

### Use when
Implementing scheduled listing sync, scheduled bulk edits, or Celery Beat job management.

### Responsibilities
- Design ScheduledJob model
- Implement Celery Beat dynamic schedules
- Build scheduler UI (create, edit, delete jobs)
- Implement timezone-aware scheduling
- Log job execution history

### Rules
- Scheduled writes must still follow the safe-external-write protocol
- Users must confirm scheduled write jobs
- Job failures must notify the user

### Usually touches
`apps/backend/app/scheduling/`, `apps/backend/celery_beat.py`, `apps/backend/app/models/scheduled_job.py`

### Must update
`TASKS.md`

### Required tests
Schedule creation tests. Execution tests. Failure handling tests.

---

## 19 admin-panel

### Use when
Building admin user management, subscription oversight, audit log viewer, or system health dashboard.

### Responsibilities
- Build admin-only API routes with role gate
- Build admin user management UI
- Build admin subscription management UI
- Build audit log viewer
- Build system health dashboard

### Rules
- Admin routes must require `role=admin` on every request
- Admin actions must be logged in audit log
- Never expose admin UI to non-admin users

### Usually touches
`apps/backend/app/routers/admin.py`, `apps/frontend/app/admin/`

### Must update
`TASKS.md`

### Required tests
Admin RBAC tests. Admin action audit log tests.

---

## 20 testing-qa

### Use when
Writing tests, running test suites, measuring coverage, or doing QA passes.

### Responsibilities
- Write backend unit tests (pytest)
- Write frontend component tests (Vitest / Testing Library)
- Write E2E tests (Playwright)
- Measure and report coverage
- Identify and document gaps

### Rules
- Backend coverage target: >80%
- Frontend coverage target: >70%
- Critical user flows must have E2E tests
- CI must fail on coverage regression

### Usually touches
`apps/backend/tests/`, `apps/frontend/__tests__/`, `apps/frontend/e2e/`, `docs/operations/TESTING.md`

### Must update
`docs/operations/TESTING.md`, `TASKS.md`

### Required tests
This skill IS about tests. All tests must pass before sprint close.

---

## 21 security-audit

### Use when
Running security reviews, fixing OWASP findings, auditing auth flows, or hardening configs.

### Responsibilities
- Run OWASP Top 10 audit
- Check for injection vulnerabilities
- Audit authentication and authorization flows
- Review secret management
- Review CORS, CSP, rate limiting configs

### Rules
- All critical findings must be fixed before release
- High findings must be tracked in SECURITY.md
- Never skip security hardening before v1.0

### Usually touches
`SECURITY.md`, `docs/technical/SECURITY_MODEL.md`, all backend route files

### Must update
`SECURITY.md`, `DECISIONS.md`

### Required tests
Security-focused test cases for all auth and write flows.

---

## 22 devops-deployment

### Use when
Configuring CI/CD, writing production Docker configs, setting up monitoring, or managing deployments.

### Responsibilities
- Write GitHub Actions CI/CD workflows
- Write production Docker Compose / Kubernetes configs
- Configure environment-specific settings
- Set up SSL termination and reverse proxy
- Write deployment runbooks

### Rules
- Production configs must not contain dev defaults
- CI must run all tests before deploy
- Never deploy with failing tests
- Rollback procedure must be documented

### Usually touches
`.github/workflows/`, `docker-compose.prod.yml`, `docs/operations/DEPLOYMENT.md`

### Must update
`docs/operations/DEPLOYMENT.md`, `docs/operations/RELEASE_CHECKLIST.md`

### Required tests
CI pipeline must pass. Health endpoints must respond after deploy.

---

## 23 observability

### Use when
Adding logging, metrics, tracing, alerting, or error tracking.

### Responsibilities
- Add structured logging (JSON) to backend
- Add request tracing (correlation IDs)
- Integrate error tracking (Sentry)
- Add performance metrics
- Build health check endpoints

### Rules
- Never log PII or secrets
- All errors must be captured with context
- Correlation IDs must flow from frontend to backend

### Usually touches
`apps/backend/app/middleware/logging.py`, `apps/backend/app/routers/health.py`

### Must update
`TASKS.md`

### Required tests
Health endpoint tests. Logging output format tests.

---

## 24 ux-polish

### Use when
Improving UI consistency, accessibility, loading states, empty states, error messages, or mobile responsiveness.

### Responsibilities
- Implement consistent design system
- Add loading skeletons
- Add empty state illustrations
- Write helpful error messages
- Ensure WCAG 2.1 AA accessibility
- Ensure mobile responsiveness

### Rules
- All interactive elements must have focus states
- All images must have alt text
- Color contrast must meet WCAG AA minimums
- All pages must be usable on mobile

### Usually touches
`apps/frontend/components/`, `apps/frontend/app/`, `apps/frontend/styles/`

### Must update
`TASKS.md`

### Required tests
Accessibility audit (axe-core). Responsive layout spot checks.
