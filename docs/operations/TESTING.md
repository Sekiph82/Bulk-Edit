# Testing Strategy

## Current Test Counts (Sprint 18)

| Test File | Tests | Status |
|---|---|---|
| `test_health.py` | 4 | PASSED |
| `test_auth.py` | 14 | PASSED |
| `test_billing.py` | 26 | PASSED |
| `test_etsy.py` | 15 | PASSED |
| `test_listings.py` | 34 | PASSED |
| `test_bulk_edit.py` | 38 | PASSED |
| `test_bulk_edit_apply.py` | 22 | PASSED |
| `test_bulk_edit_revert.py` | 28 | PASSED |
| `test_bulk_edit_inventory.py` | 19 | PASSED |
| `test_bulk_edit_media.py` | 25 | PASSED |
| `test_bulk_edit_variation.py` | 47 | PASSED |
| `test_ai_tools.py` | 32 | PASSED |
| `test_csv_tools.py` | 49 | PASSED |
| `test_dynamic_pricing.py` | 50 | PASSED |
| `test_seed_local_superusers.py` | 23 | PASSED |
| `test_windows_batch_readiness.py` | 12 | PASSED |
| `test_scheduled_jobs.py` | 41 | PASSED |
| `test_admin_panel.py` | 42 | PASSED |
| `test_security_hardening.py` | 45 | PASSED |
| **Total** | **566** | **ALL PASSED** |

---

## Coverage Targets

| Layer | Target | Current |
|---|---|---|
| Backend (pytest) | > 80% | ~85% (estimated) |
| Frontend (Vitest) | > 70% | Not yet configured |
| E2E (Playwright) | Critical flows | Not yet configured |

---

## Backend Tests (pytest)

### Location

`apps/backend/tests/`

### Test Database

Tests use an **in-memory SQLite** database with `aiosqlite`. No PostgreSQL required for tests.

Connection string: `sqlite+aiosqlite:///file:testdb?mode=memory&cache=shared&uri=true`

Alembic migrations are **not** applied in tests — `SQLAlchemy.metadata.create_all` is used instead for speed.

### Running Tests

```bash
# Host (Windows)
cd apps/backend
python -m pytest --tb=short -q

# Via Docker
docker compose -p bulk-edit exec backend pytest --tb=short -q

# With coverage
cd apps/backend
python -m pytest --cov=app --cov-report=term-missing -q

# Single test file
python -m pytest tests/test_auth.py -v

# Single test
python -m pytest tests/test_auth.py::test_register_success -v
```

### Key Fixtures (conftest.py)

| Fixture | Scope | Description |
|---|---|---|
| `db_engine` | function | SQLite in-memory async engine with all tables created |
| `db_session` | function | Async database session, rolled back after each test |
| `client` | function | `httpx.AsyncClient` with `get_db` dependency overridden to use test DB |

### Test Markers

Tests are async and use `pytest-asyncio` in auto mode (configured in `pyproject.toml`).

No explicit `@pytest.mark.asyncio` decorator needed — all `async def test_*` functions are detected automatically.

### Security Tests (test_security_hardening.py)

Covers:
- **Unauthenticated access**: 11 protected endpoints return 401/403 without token
- **JWT tampering**: tampered signatures and empty tokens rejected
- **Superuser gate**: admin endpoints return 403 for regular users
- **No secrets in responses**: no `password_hash`, `access_token_enc`, `stripe_secret`
- **Org isolation**: users cannot see other organizations' data (listings, bulk sessions, AI, CSV, DP, scheduled jobs)
- **SQL injection**: injection in `title`, `tag`, `sort_by` params returns 422 or empty results, never 500
- **Oversized IDs**: nonexistent and overlong IDs return 404/422, never 500
- **Input validation**: XSS in email rejected, short passwords rejected, duplicate email returns 409
- **Stack trace safety**: error responses do not expose Python tracebacks

---

## Frontend Tests (Vitest + Testing Library)

Not yet configured. To set up:

```bash
cd apps/frontend
npm install --save-dev vitest @testing-library/react @testing-library/jest-dom
```

Add to `package.json`:
```json
{
  "scripts": {
    "test": "vitest run",
    "test:watch": "vitest",
    "test:coverage": "vitest run --coverage"
  }
}
```

Target: `apps/frontend/__tests__/` directory.

Priority test areas:
- `ThemeProvider` — system/light/dark preference, `localStorage` key, `data-theme` attribute
- `AnimatedProductDemo` — renders without crashing, respects `prefers-reduced-motion`
- Form validation in `login/page.tsx` and `register/page.tsx`
- API client helpers in `lib/api.ts`

---

## E2E Tests (Playwright)

Not yet configured. To set up:

```bash
cd apps/frontend
npm install --save-dev @playwright/test
npx playwright install
```

Required flows for Sprint 19:
- User registration → dashboard
- Login and logout
- Etsy shop connection (mocked OAuth)
- Listing sync (mocked Etsy API)
- Bulk edit flow: select → add changes → preview → apply
- Magic Revert flow
- Stripe checkout (Stripe test mode)
- Admin panel access (superuser only)

---

## CI Test Execution

GitHub Actions workflow (`.github/workflows/test.yml` — to be created in Sprint 19):

```yaml
jobs:
  backend-tests:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.12"
      - run: cd apps/backend && pip install -r requirements-dev.txt
      - run: cd apps/backend && pytest --tb=short -q

  frontend-build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: "20"
      - run: cd apps/frontend && npm ci
      - run: cd apps/frontend && npm run build
```

---

## Health Endpoints

Available for monitoring and readiness checks:

| Endpoint | Purpose | Response |
|---|---|---|
| `GET /api/v1/health` | Liveness — is the process running? | `{"status": "ok", "service": "bulk-edit-api"}` |
| `GET /api/v1/health/db` | DB connectivity check | `{"status": "ok", "database": "connected"}` or 503 |
| `GET /api/v1/health/redis` | Redis connectivity check | `{"status": "ok", "redis": "connected"}` or 503 |
| `GET /api/v1/health/ready` | Readiness probe — ready to serve traffic? | `{"status": "ready", "database": "connected"}` or 503 |

Use `/health/ready` for Kubernetes/Docker readiness probes and load balancer health checks.
