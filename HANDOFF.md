# HANDOFF.md — Session Handoff

## Last Session

**Date:** 2026-06-26
**Sprint:** Sprint 13 — AI Tools — COMPLETE
**Completed:** Installed `motion` v12. Created `AnimatedProductDemo.tsx` (5-phase animation: idle → select → edit panel → preview → safety strip; easeOut only; reduced-motion support; aria-hidden; zero API calls). Rewrote `app/page.tsx` with 2-column hero layout (headline+CTAs+trust strip left, demo right), workflow strip below. Updated DESIGN.md motion rules. Updated design-system/pages/home.md. Lint clean, build 14 routes zero errors. Committed and pushed.

## Previous Session

**Date:** 2026-06-26
**Sprint:** Landing Animation Sprint — AnimatedProductDemo — COMPLETE
**Completed:** npm install + full build baseline. Fixed tsconfig target (ES2017). Fixed billing/page.tsx Suspense wrapper. Removed emoji from empty states across shops/listings. Removed sprint labels from media operation labels. Replaced emoji check/cross in pricing with SVG. Added loading="lazy" to all thumbnail imgs. Added focus rings to all buttons across all 9 pages. Human-readable op labels in variations job history and media confirm modal. Build: 14 routes, zero errors. Committed and pushed.

## Current State

**Backend (`apps/backend/`):**
- `app/models/bulk_edit_variation_job.py` — job status machine + preview/success/failure/skipped counters
- `app/models/bulk_edit_variation_preview_item.py` — per-listing before/after/diff JSON, validation_status; unique (job, listing)
- `app/models/bulk_edit_variation_result.py` — per-listing result with status, request/response payload, error
- `app/models/listing_variation_backup_snapshot.py` — local_variations_snapshot + etsy_inventory_snapshot JSON, etsy_shop_id FK
- `alembic/versions/0009_create_bulk_edit_variation_tables.py` — migration for 4 tables
- `app/services/etsy_variation_write.py` — fetch_etsy_listing_inventory, put_etsy_listing_inventory, normalize_etsy_inventory_tree (strips deleted/read-only), patch_inventory_tree_for_variation_operation (8 ops with selector), _product_matches_selector; EtsyVariationWriteError; MAX_SKU_LENGTH=32
- `app/schemas/bulk_edit_variation.py` — VariationJobCreate (validated), VariationJobOut, VariationPreviewItemOut, VariationPreviewPageOut, VariationResultOut, VariationResultPageOut, VariationBackupSnapshotOut
- `app/services/bulk_edit_variation.py` — create_variation_job, generate_variation_preview, apply_variation_job (status check → Etsy config → no invalid items → fetch Etsy inventory → backup → normalize → patch → PUT → update local on success only → audit logs), list/get/preview/results/backups helpers
- `app/api/v1/bulk_edit_variations.py` — 8 endpoints under /api/v1/bulk-edit/variations
- `tests/test_bulk_edit_variation.py` — 47 tests (unit: normalize/patch/selector/validate/preview; API: auth/validation/create/preview/apply gates/apply flow/org isolation/audit)

**Frontend (`apps/frontend/`):**
- `app/variations/page.tsx` — listing selector (filtered to has_variations=true), 8-operation picker, amount/SKU/find-replace/availability inputs, optional selector (property_name + value_name), Preview button, before/after variation table, APPLY VARIATIONS confirm modal, results panel, job history. Op labels now human-readable in job history.
- `lib/api.ts` — VariationJob, VariationPreviewItem, VariationPreviewPage, VariationResult, VariationResultPage, VariationBackupSnapshot types + 8 helpers
- `app/dashboard/page.tsx` — Variation Editor card added linking to /variations
- All pages polished (Productization UI Sprint): focus rings on all buttons, lazy thumbnails, no emoji in data UI, no sprint labels, SVG icons in pricing, Suspense wrappers on billing
- `tsconfig.json` — added `"target": "ES2017"` (was defaulting to ES3, broke Set spread)
- Build: 14 routes, zero type errors, zero lint errors

**What NOT implemented in Sprint 12 (by design):**
- Variation revert — backup snapshots created to enable Sprint 13 revert
- AI variation suggestions — Sprint 13
- Celery async apply — inline synchronous MVP

## Safety Gates (Sprint 12)

All enforced in `apply_variation_job()`:
1. Job must belong to organization (404 if not) — checked FIRST
2. Job must be `preview_ready` (400 if not) — checked BEFORE Etsy config
3. `ETSY_CLIENT_ID` must be configured (503 if not) — checked AFTER status gate
4. No invalid preview items (400 if any) — checked before writes
5. Per-listing: fetch current Etsy inventory tree (GET) before patching
6. Per-listing: backup snapshot (local + etsy) created BEFORE any Etsy write
7. Normalize tree (strip deleted/read-only) before PUT
8. Local ListingVariation rows updated ONLY after Etsy PUT success
9. Audit log on apply start + apply finish
10. Partial failure supported — each listing gets its own BulkEditVariationResult row
11. Backup snapshots never deleted

## Fetch-Patch-Put Pattern

Never construct variation tree from local data alone. Always:
1. `GET /v3/application/shops/{shop_id}/listings/{listing_id}/inventory` → fetch current tree
2. Deep copy and patch in memory (apply operation to matching products)
3. `normalize_etsy_inventory_tree()` — strip `is_deleted=True`, strip read-only fields
4. `PUT /v3/application/shops/{shop_id}/listings/{listing_id}/inventory` → write full tree back

## Port Summary

| Service | Host | Container |
|---|---|---|
| Frontend | 3100 | 3000 |
| Backend | 8100 | 8000 |
| PostgreSQL | 55432 | 5432 |
| Redis | 56379 | 6379 |

## Current State

**Sprint 13 additions (AI Tools):**
- `apps/backend/app/services/ai_provider.py` — MockProvider/OpenAIProvider/AnthropicProvider; default=mock
- `apps/backend/app/services/ai_prompts.py` — 5 prompt builders
- `apps/backend/app/models/ai_session.py`, `ai_suggestion.py`, `ai_usage_log.py` — 3 new models
- `apps/backend/alembic/versions/0010_create_ai_tools_tables.py` — migration
- `apps/backend/app/schemas/ai.py` — 6 schemas
- `apps/backend/app/services/ai_tools.py` — full service layer
- `apps/backend/app/api/v1/ai.py` — 9 endpoints
- `apps/backend/tests/test_ai_tools.py` — 32 tests (all mocked)
- `apps/frontend/lib/api.ts` — AI types + 9 helpers
- `apps/frontend/app/ai/page.tsx` — full AI tools page
- `apps/frontend/app/dashboard/page.tsx` — AI Optimizer card
- Full suite: 304/304 PASSED; build: 15 routes, zero errors

## Next Task

**Sprint 14: CSV Import / Export**

Implement CSV export of listings and CSV import with validation, preview, and bulk-apply.

Context:
- Existing Listing model has all fields needed for CSV columns
- Export: SELECT listings → stream CSV (title, description, tags, price, quantity, state, sku, etc.)
- Import: upload CSV → validate rows → show diff preview → user confirms → create BulkEditSession
- No direct Etsy writes in this sprint — import creates a BulkEditSession for user to apply
- CSVJob model tracks import jobs (uploaded, validated, preview_ready, applied)

Implement:
- CSVJob model + Alembic migration 0011
- Export endpoint: GET /api/v1/csv/export?shop_id=... → streams CSV file
- Import endpoint: POST /api/v1/csv/import (multipart upload) → validates + creates CSVJob
- Preview endpoint: GET /api/v1/csv/jobs/{id}/preview → diff view
- Convert endpoint: POST /api/v1/csv/jobs/{id}/convert → creates BulkEditSession
- Frontend: /csv page with export button + CSV upload + diff table + convert button
- 20+ tests

## Next Prompt

```
Read CLAUDE.md, TASKS.md, SKILLS.md, PROJECT_STATUS.md, HANDOFF.md, DECISIONS.md, LIMIT_PROTOCOL.md.

Start Sprint 14: CSV Import/Export — implement CSV export of listings and CSV import with validation, preview, and conversion to BulkEditSession. No direct Etsy writes in this sprint.

Backend: CSVJob model, /api/v1/csv/* endpoints, export + import + preview + convert.
Frontend: /csv page with export + upload + diff preview + convert.
Tests: 20+ tests.

Active skills: 07 backend-api, 06 database-modeling, 20 testing-qa, 01 documentation-handoff.
```

## Dev Startup Scripts

Four Windows batch files at project root:

| File | Who uses it | What it does |
|---|---|---|
| `setup-and-start.bat` | Friend / reviewer | Installs Git + Docker if missing, clones repo, starts app, opens browser at http://localhost:3100 |
| `setup-and-start-clean.bat` | Friend / reviewer | Same as above + destroys DB volumes (requires YES confirmation) |
| `start-dev.bat` | Developer (already cloned) | Stops old containers, rebuilds, streams logs — no tool install |
| `start-dev-clean.bat` | Developer (already cloned) | Same + destroys DB volumes (requires YES confirmation) |

**ASCII-only scripts:** all .bat files must remain plain ASCII. No Unicode, no box-drawing chars, no long dashes, no chcp 65001.

**Docker Desktop auto-start:** all scripts automatically start Docker Desktop and poll `docker info` every 5 seconds (max 180s) before running any compose command.

**Docker project isolation:** all scripts force `docker compose -p bulk-edit` to prevent accidental interference with other Docker Compose projects.

## Known Issues

- Etsy access token auto-refresh not implemented. Logs warning but uses token. Full refresh deferred to future sprint.
- `fetch_listing_videos` is best-effort — returns empty list on 404/405.
- Sync runs inline in HTTP thread. Celery background task deferred to a future sprint.
- Frontend npm not installed — `node_modules/` absent. Run `npm install` inside `apps/frontend` or `docker compose up`.
- Video upload/delete NOT supported — Etsy requires direct file upload; URL-based not available. Stubs return 501. Deferred to Sprint 13+.
- Image reorder NOT supported — Etsy has no atomic reorder endpoint. Deferred.
- Variation revert NOT implemented — backup snapshots created in Sprint 12; revert deferred to Sprint 13.
- AuditLog model uses `extra_data` attribute in Python (SQLAlchemy reserved `metadata` name), stored as `metadata` column in DB.
- `anyio==4.6.2` in requirements-dev.txt is yanked — works fine, upgrade when 4.7.0 stable.

## Push Status

Pushed successfully to: https://github.com/Sekiph82/Bulk-Edit (main)
Commit: feat: add variation editor (Sprint 12)
