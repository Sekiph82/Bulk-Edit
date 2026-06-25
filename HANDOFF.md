# HANDOFF.md — Session Handoff

## Last Session

**Date:** 2026-06-26
**Sprint:** Productization UI Sprint — Design System Prep — COMPLETE
**Completed:** Impeccable v3.1.0 + UI UX Pro Max v2.2.3 installed project-locally. PRODUCT.md, DESIGN.md, design-system/MASTER.md, 6 page-specific design overrides (design-system/pages/), docs/design/PRODUCT_UI_DIRECTION.md, docs/design/UI_AUDIT.md created. Light cleanup: sprint labels + API debug panel + disabled roadmap cards removed from homepage and dashboard. 272/272 backend tests passing (no backend files touched). Committed and pushed.

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
- `app/variations/page.tsx` — listing selector (filtered to has_variations=true), 8-operation picker, amount/SKU/find-replace/availability inputs, optional selector (property_name + value_name), Preview button, before/after variation table, APPLY VARIATIONS confirm modal, results panel, job history
- `lib/api.ts` — VariationJob, VariationPreviewItem, VariationPreviewPage, VariationResult, VariationResultPage, VariationBackupSnapshot types + 8 helpers
- `app/dashboard/page.tsx` — Variation Editor card added linking to /variations

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

## Next Task

**Productization UI Sprint: Apply Design System to All Customer-Facing Pages**

Read PRODUCT.md, DESIGN.md, design-system/MASTER.md, and docs/design/UI_AUDIT.md before starting.

Pages to redesign (in priority order):
1. `apps/frontend/app/page.tsx` — Homepage (marketing landing, minimal)
2. `apps/frontend/app/dashboard/page.tsx` — Dashboard (clean feature grid, no roadmap)
3. `apps/frontend/app/listings/page.tsx` — Listings grid (table cleanup, empty state, lazy thumbnails)
4. `apps/frontend/app/bulk-edit/page.tsx` — Bulk edit (2-column, preview table, confirm modal)
5. `apps/frontend/app/media/page.tsx` — Media editor (compact, backup warning)
6. `apps/frontend/app/variations/page.tsx` — Variation editor (same pattern as media)
7. `apps/frontend/app/shops/page.tsx` — Shops (connect/disconnect, sync status)
8. `apps/frontend/app/pricing/page.tsx` — Pricing (clean plan comparison)
9. `apps/frontend/app/billing/page.tsx` — Billing (current plan, usage, portal button)

Key fixes per UI audit:
- P0: Remove any remaining sprint labels / API debug panels (already done for page.tsx + dashboard)
- P1: Add focus rings to all interactive elements (`focus:outline-none focus:ring-2 focus:ring-indigo-300`)
- P1: Add `<label>` to all form inputs
- P1: Replace emoji icons with SVG throughout
- P1: Add loading states / skeleton rows to async data tables
- P1: Apply consistent Inter type scale
- P2: Add empty states to all data tables
- P2: Add `loading="lazy"` to all thumbnails
- P3: Extract StatusBadge, AppNav to shared components

**Sprint 13: AI Tools**

Implement AI-powered listing optimizations using OpenAI GPT-4o and/or Anthropic Claude.

Context:
- Listing model has `title`, `description`, `tags`, `materials`, `taxonomy_id` — all candidate AI fields
- ListingImage has `alt_text` — candidate for AI alt text
- AI output must NEVER be applied directly to Etsy — preview + user approval required
- Feature gate: AI tools are a paid feature (Pro plan minimum)
- No new Etsy writes in this sprint — just generate suggestions and store them for user review

Implement:
- AI service (app/services/ai_tools.py) using OpenAI + Anthropic clients
- Endpoints: POST /api/v1/ai/title, /api/v1/ai/description, /api/v1/ai/tags, /api/v1/ai/alt-text, /api/v1/ai/seo-score
- AI suggestions stored in AISession model (org-scoped, listing_id, field, suggestion, accepted_at)
- Frontend: AI tools panel showing suggestions with Accept / Reject per field
- All AI calls mocked in tests (no real API calls in CI)
- 20+ tests

## Next Prompt

```
Read CLAUDE.md, TASKS.md, SKILLS.md, PROJECT_STATUS.md, HANDOFF.md, DECISIONS.md, LIMIT_PROTOCOL.md.

Start Sprint 13: AI Tools — implement AI-powered listing title, description, tag, alt-text optimization using OpenAI/Anthropic. AI output must be previewed and user-approved before applying. Feature-gated to Pro plan. All AI calls mocked in tests. No direct Etsy writes in this sprint.

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
