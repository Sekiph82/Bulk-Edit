# Beta Readiness Smoke Matrix

**M19.01.** Formal, categorized checklist for verifying Bulk Edit is healthy before/after a
production deploy and before wider beta expansion. Automated where safe (`scripts/smoke_test_deployment.sh`
/ `.ps1` — read-only route/health checks, no secrets, no Etsy calls); everything that writes to Etsy,
runs a real bulk operation, or needs a human eye stays **owner-run**.

Each row: **Objective** (what we're proving) · **Route** · **Data needed** · **Owner-run or
Automated** · **Destructive?** · **Expected result** · **Evidence to capture** · **Pass/Fail**.

Run the automated section first (`bash scripts/smoke_test_deployment.sh https://app.bulkeditapp.com
https://api.bulkeditapp.com`, or the `.ps1` equivalent on Windows) — it covers every row marked
**Automated** in one pass. Owner-run rows are done manually, one at a time, stopping immediately on
an unexpected result (see the runbooks in this directory for exact stop conditions per workflow).

---

## Auth

| Objective | Route | Data needed | Run | Destructive | Expected | Evidence | Pass/Fail |
|---|---|---|---|---|---|---|---|
| Login page loads | `/login` | none | Automated | No | 200 | script output | |
| Registered user can log in | `/login` | test account credentials | Owner-run | No | Redirects to dashboard | screenshot | |
| Invalid password rejected | `/login` | test account | Owner-run | No | Error shown, no session created | screenshot | |
| Session persists across reload | any authenticated page | logged-in session | Owner-run | No | Still logged in after refresh | — | |

## Private Beta registration gate

| Objective | Route | Data needed | Run | Destructive | Expected | Evidence | Pass/Fail |
|---|---|---|---|---|---|---|---|
| `/register` redirects while Private Beta is enabled | `/register` | none | Automated | No | `307` → `/private-beta` | script output | |
| `/signup`, `/get-started` also redirect | `/signup`, `/get-started` | none | Owner-run (not in the automated script) | No | Redirect to `/private-beta` | manual curl/browser | |
| `/private-beta` page itself loads | `/private-beta` | none | Automated | No | 200 | script output | |

## Connected Shops

| Objective | Route | Data needed | Run | Destructive | Expected | Evidence | Pass/Fail |
|---|---|---|---|---|---|---|---|
| Connected Shops page loads | `/account/connected-shops` (or `/shops`, redirects) | logged-in session | Owner-run | No | Shows connected shop(s) | screenshot | |
| Connect Etsy button present, not clicked in an automated/CI context | `/account/connected-shops` | none | Owner-run only | **Yes if clicked** — starts real OAuth | Button visible | — | |

## Shop sync

| Objective | Route | Data needed | Run | Destructive | Expected | Evidence | Pass/Fail |
|---|---|---|---|---|---|---|---|
| Sync Listings completes | `/listings` → Sync button | connected shop | **Owner-run only** | Reads Etsy, writes local DB only | Listing count matches Etsy Shop Manager | before/after counts | |

## Listings grid

| Objective | Route | Data needed | Run | Destructive | Expected | Evidence | Pass/Fail |
|---|---|---|---|---|---|---|---|
| Listings page loads | `/listings` | none (page shell) | Automated | No | 200 | script output | |
| Grid renders synced listings | `/listings` | synced shop | Owner-run | No | Rows match Etsy | screenshot | |
| Filters/search/pagination work | `/listings` | synced shop | Owner-run | No | Results narrow correctly | — | |

## Product detail

| Objective | Route | Data needed | Run | Destructive | Expected | Evidence | Pass/Fail |
|---|---|---|---|---|---|---|---|
| Product detail page loads | `/listings/{id}` | a real listing id | Owner-run (dynamic route, no safe id to hardcode) | No | Shows title/price/images | screenshot | |
| Image gallery renders (M13.02) | `/listings/{id}` | listing with synced photos | Owner-run | No | Full thumbnail grid, not just one image | screenshot | |

## Listing Health

| Objective | Route | Data needed | Run | Destructive | Expected | Evidence | Pass/Fail |
|---|---|---|---|---|---|---|---|
| Listing Health page loads | `/listing-health` | none (page shell) | Automated | No | 200 | script output | |
| Scores/issues render for synced listings | `/listing-health` | synced shop | Owner-run | No | Real scores, not zeros | screenshot | |
| Issue detail expands (M10.01) | `/listing-health` | listing with issues | Owner-run | No | Issue pills show, "Show all N" works if >3 | screenshot | |

## Shop Insights

| Objective | Route | Data needed | Run | Destructive | Expected | Evidence | Pass/Fail |
|---|---|---|---|---|---|---|---|
| Insights page loads | `/insights` | none (page shell) | Automated | No | 200 | script output | |
| Affected Listings sections render (M10.03) | `/insights` | synced shop with gaps (missing tags/photos/etc.) | Owner-run | No | Real listings shown, not fabricated | screenshot | |

## Bulk Edit preview

| Objective | Route | Data needed | Run | Destructive | Expected | Evidence | Pass/Fail |
|---|---|---|---|---|---|---|---|
| Bulk Edit page loads | `/bulk-edit` | none (page shell) | Automated | No | 200 | script output | |
| Preview computes before/after diff | `/bulk-edit` | selected listing(s) | Owner-run | No — preview only | Diff shown, nothing written | screenshot | |

## Title write / revert — owner-run only

| Objective | Route | Data needed | Run | Destructive | Expected | Evidence | Pass/Fail |
|---|---|---|---|---|---|---|---|
| Single-listing title write succeeds | `/bulk-edit` | one real listing, owner approval | **Owner-run only** | **Yes — live Etsy write** | Etsy Shop Manager reflects new title | Etsy screenshot + app result card | |
| Magic Revert restores it | `/bulk-edit` or `/magic-revert` | the job above | **Owner-run only** | **Yes — live Etsy write** | Etsy Shop Manager reflects original title | Etsy screenshot + app result card | |

## Price write / revert — owner-run only

| Objective | Route | Data needed | Run | Destructive | Expected | Evidence | Pass/Fail |
|---|---|---|---|---|---|---|---|
| Single-listing price write succeeds | `/bulk-edit` | one real listing, owner approval | **Owner-run only** | **Yes — live Etsy write** | Etsy Shop Manager reflects new price | Etsy screenshot + app result card | |
| Magic Revert restores it | `/bulk-edit` or `/magic-revert` | the job above | **Owner-run only** | **Yes — live Etsy write** | Etsy Shop Manager reflects original price | Etsy screenshot + app result card | |

See `MAGIC_REVERT_RUNBOOK.md` and `OWNER_BULK_EDIT_RUNBOOK.md` for the exact safe procedure.

## Magic Revert History

| Objective | Route | Data needed | Run | Destructive | Expected | Evidence | Pass/Fail |
|---|---|---|---|---|---|---|---|
| History page loads | `/magic-revert` | none (page shell) | Automated | No | 200 | script output | |
| Prior apply jobs listed with correct revert-eligibility | `/magic-revert` | org with apply-job history | Owner-run | No — read-only view | `can_revert`/reasons match actual state | screenshot | |
| Activity & Audit page loads | `/account/activity` | none (page shell) | Owner-run (route not in automated list yet) | No | 200 | screenshot | |

## Media (read)

| Objective | Route | Data needed | Run | Destructive | Expected | Evidence | Pass/Fail |
|---|---|---|---|---|---|---|---|
| Media page loads | `/media` | none (page shell) | Automated | No | 200 | script output | |
| Listing picker shows thumbnails (M03.04) | `/media` | synced shop | Owner-run | No | Real thumbnails, pagination works | screenshot | |
| `add_image`/`add_video` selectable; `replace_*`/`delete_*` disabled (M13.04) | `/media` | none | Owner-run | No | Delete/replace options show "coming soon — no restore yet" | screenshot | |

## Variations (read)

| Objective | Route | Data needed | Run | Destructive | Expected | Evidence | Pass/Fail |
|---|---|---|---|---|---|---|---|
| Variations page loads | `/variations` | none (page shell) | Automated | No | 200 | script output | |
| Variation Data matrix renders (M15.01) | `/variations` | listing with `has_variations=true` and synced rows | Owner-run | No | Real property/value/price/qty/SKU rows | screenshot | |
| Diagnostics column shows validation messages (M15.05) | `/variations` | a preview with a warning/invalid item | Owner-run | No | Message text, not a bare badge | screenshot | |

## Billing plan display

| Objective | Route | Data needed | Run | Destructive | Expected | Evidence | Pass/Fail |
|---|---|---|---|---|---|---|---|
| Billing page loads | `/billing` (redirects to `/account/billing`) | logged-in session | Automated (route shell only) | No | 200 | script output | |
| Effective plan shown correctly (comp-grant aware) | `/account/billing` | comp-grant or paid account | Owner-run | No | Matches `get_effective_plan()`, not raw `Subscription.plan` | screenshot | |

## Usage/Credits

| Objective | Route | Data needed | Run | Destructive | Expected | Evidence | Pass/Fail |
|---|---|---|---|---|---|---|---|
| Usage page loads | `/account/usage` | logged-in session | Owner-run (route not in automated list yet) | No | Real used/limit numbers | screenshot | |
| Credits page loads | `/account/credits` | logged-in session | Owner-run | No | Real AI credit balance | screenshot | |

## Account pages

| Objective | Route | Data needed | Run | Destructive | Expected | Evidence | Pass/Fail |
|---|---|---|---|---|---|---|---|
| Account overview loads | `/account` | none (page shell) | Automated | No | 200 | script output | |
| Shops page loads | `/shops` | none (page shell) | Automated | No | 200 | script output | |
| Owner console loads (superuser only) | `/owner` | none (page shell) | Automated | No | 200 | script output | |

## Mobile/responsive pass

| Objective | Route | Data needed | Run | Destructive | Expected | Evidence | Pass/Fail |
|---|---|---|---|---|---|---|---|
| Core pages usable at mobile width | `/dashboard`, `/listings`, `/bulk-edit`, `/account` | logged-in session, narrow viewport | Owner-run | No | No horizontal scroll, controls reachable | screenshots at ~375px width | |

## Error / empty / loading states

| Objective | Route | Data needed | Run | Destructive | Expected | Evidence | Pass/Fail |
|---|---|---|---|---|---|---|---|
| No synced listings shows a truthful empty state, not a fake table | `/listings`, `/listing-health`, `/insights` | fresh org, no sync yet | Owner-run | No | Honest "no data" message, not fabricated rows | screenshot | |
| API error shows a real message, not a silent blank page | any data-driven page | simulate by disconnecting network briefly | Owner-run | No | Visible error text | screenshot | |

## Rate limit behavior

| Objective | Route | Data needed | Run | Destructive | Expected | Evidence | Pass/Fail |
|---|---|---|---|---|---|---|---|
| A 429 from Etsy during a real write is retried and surfaced correctly | Bulk Edit apply on many listings | large real batch, owner approval | **Owner-run only** | **Yes — live Etsy write** | Retry-count-aware message on any residual failure, no silent data loss | app result card | |

See `RATE_LIMIT_RUNBOOK.md`.

## Help/support links

| Objective | Route | Data needed | Run | Destructive | Expected | Evidence | Pass/Fail |
|---|---|---|---|---|---|---|---|
| Support page loads | `/account/support` | logged-in session | Owner-run (route not in automated list yet) | No | Links resolve, no dead links | screenshot | |

## Security / no-secret logging

| Objective | Route | Data needed | Run | Destructive | Expected | Evidence | Pass/Fail |
|---|---|---|---|---|---|---|---|
| No token/secret in any API response body | any authenticated API call | logged-in session, DevTools | Owner-run | No | No `access_token`/`refresh_token`/`*_secret`/`Authorization` value in response JSON | DevTools network export | |
| `/docs`, `/redoc` disabled in production | `https://api.bulkeditapp.com/docs`, `/redoc` | none | Owner-run (add to automated script if this becomes routine) | No | 404 (`DEBUG=false`) | curl output | |

---

## Running the automated section

```bash
bash scripts/smoke_test_deployment.sh https://app.bulkeditapp.com https://api.bulkeditapp.com
```

```powershell
.\scripts\smoke_test_deployment.ps1 -FrontendUrl https://app.bulkeditapp.com -BackendUrl https://api.bulkeditapp.com
```

Both scripts are read-only, need no secrets, and never call Etsy. Last confirmed run (2026-08-30):
26/26 checks passed against production.
