# Testing Strategy

## Coverage Targets

| Layer | Target |
|---|---|
| Backend (pytest) | > 80% |
| Frontend (Vitest) | > 70% |
| E2E (Playwright) | Critical user flows |

## Backend Tests (pytest)

Location: `apps/backend/tests/`

Structure:
```
tests/
  unit/
    test_auth.py
    test_bulk_engine.py
    test_ai_tools.py
    test_billing.py
    test_etsy_client.py
    test_csv.py
  integration/
    test_listings_api.py
    test_bulk_edit_api.py
    test_webhook_handler.py
  conftest.py         # fixtures, test DB
```

Run:
```bash
cd apps/backend
pytest --cov=app --cov-report=term-missing
```

Key fixtures:
- `test_db` — isolated PostgreSQL test database (Alembic applied)
- `test_redis` — isolated Redis instance
- `auth_headers` — valid JWT headers for test user
- `mock_etsy_client` — mock Etsy API responses
- `mock_stripe` — mock Stripe API

## Frontend Tests (Vitest + Testing Library)

Location: `apps/frontend/__tests__/`

Run:
```bash
cd apps/frontend
npm test
npm run test:coverage
```

Focus:
- Component rendering
- Form validation
- Hook behavior
- API client mocking

## E2E Tests (Playwright)

Location: `apps/frontend/e2e/`

Run:
```bash
cd apps/frontend
npm run test:e2e
```

Required flows:
- User registration and email verification
- Login and logout
- Etsy shop connection (mocked)
- Listing sync (mocked)
- Bulk edit flow end-to-end
- Stripe checkout (Stripe test mode)
- Magic Revert flow

## CI Test Execution

```yaml
# .github/workflows/test.yml (Sprint 18)
- Run backend pytest
- Run frontend Vitest
- Run Playwright E2E (headed: false)
- Fail build if coverage drops below targets
```
