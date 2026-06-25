# Database Schema

Database: PostgreSQL 16
ORM: SQLAlchemy 2.x
Migrations: Alembic

All tables include: `id` (UUID), `created_at`, `updated_at`.

---

## users

| Column | Type | Notes |
|---|---|---|
| id | UUID PK | |
| email | VARCHAR(255) UNIQUE NOT NULL | |
| password_hash | VARCHAR(255) NOT NULL | bcrypt |
| is_verified | BOOLEAN DEFAULT false | |
| is_active | BOOLEAN DEFAULT true | |
| role | VARCHAR(20) DEFAULT 'user' | 'user' or 'admin' |
| created_at | TIMESTAMP | |
| updated_at | TIMESTAMP | |

---

## organizations

| Column | Type | Notes |
|---|---|---|
| id | UUID PK | |
| name | VARCHAR(255) NOT NULL | |
| owner_id | UUID FK → users.id | |
| created_at | TIMESTAMP | |
| updated_at | TIMESTAMP | |

---

## organization_members

| Column | Type | Notes |
|---|---|---|
| id | UUID PK | |
| organization_id | UUID FK → organizations.id CASCADE | |
| user_id | UUID FK → users.id CASCADE | |
| role | VARCHAR(20) DEFAULT 'member' | 'owner', 'admin', 'member' |
| created_at | TIMESTAMP | |

---

## subscriptions (Sprint 3 — IMPLEMENTED)

| Column | Type | Notes |
|---|---|---|
| id | UUID PK | VARCHAR(36) |
| organization_id | UUID FK → organizations.id CASCADE | UNIQUE — one sub per org |
| plan | VARCHAR(50) DEFAULT 'free' | free, basic_monthly, pro_monthly, basic_yearly, pro_yearly |
| status | VARCHAR(50) DEFAULT 'free' | free, active, trialing, past_due, canceled, incomplete, unpaid |
| stripe_customer_id | VARCHAR(255) nullable | indexed |
| stripe_subscription_id | VARCHAR(255) nullable | indexed |
| stripe_price_id | VARCHAR(255) nullable | |
| current_period_start | TIMESTAMP nullable | |
| current_period_end | TIMESTAMP nullable | |
| cancel_at_period_end | BOOLEAN DEFAULT false | |
| created_at | TIMESTAMP | |
| updated_at | TIMESTAMP | |

## billing_events (Sprint 3 — IMPLEMENTED)

| Column | Type | Notes |
|---|---|---|
| id | UUID PK | |
| organization_id | UUID FK → organizations.id SET NULL | nullable |
| stripe_event_id | VARCHAR(255) | UNIQUE indexed — idempotency key |
| event_type | VARCHAR(100) | indexed |
| payload | JSON | full Stripe event |
| processed_at | TIMESTAMP nullable | null if processing failed |
| created_at | TIMESTAMP | |

## usage_counters (Sprint 3 — IMPLEMENTED)

| Column | Type | Notes |
|---|---|---|
| id | UUID PK | |
| organization_id | UUID FK → organizations.id CASCADE | indexed |
| period_key | VARCHAR(7) | e.g. "2026-06" |
| listings_synced | INTEGER DEFAULT 0 | |
| bulk_edits_used | INTEGER DEFAULT 0 | |
| ai_credits_used | INTEGER DEFAULT 0 | |
| media_assets_used | INTEGER DEFAULT 0 | |
| created_at | TIMESTAMP | |
| updated_at | TIMESTAMP | |

Unique constraint: (organization_id, period_key) |

---

## etsy_shops

| Column | Type | Notes |
|---|---|---|
| id | UUID PK | |
| organization_id | UUID FK → organizations.id | |
| etsy_shop_id | VARCHAR(255) UNIQUE NOT NULL | |
| shop_name | VARCHAR(255) | |
| is_connected | BOOLEAN DEFAULT true | |
| last_synced_at | TIMESTAMP | |
| created_at | TIMESTAMP | |
| updated_at | TIMESTAMP | |

---

## etsy_tokens

| Column | Type | Notes |
|---|---|---|
| id | UUID PK | |
| etsy_shop_id | UUID FK → etsy_shops.id | |
| access_token_enc | TEXT NOT NULL | encrypted |
| refresh_token_enc | TEXT NOT NULL | encrypted |
| expires_at | TIMESTAMP NOT NULL | |
| scopes | VARCHAR(500) | |
| created_at | TIMESTAMP | |
| updated_at | TIMESTAMP | |

---

## listings

| Column | Type | Notes |
|---|---|---|
| id | UUID PK | |
| etsy_shop_id | UUID FK → etsy_shops.id | |
| etsy_listing_id | BIGINT UNIQUE NOT NULL | |
| title | TEXT | |
| description | TEXT | |
| price | DECIMAL(10,2) | |
| quantity | INTEGER | |
| tags | TEXT[] | PostgreSQL array |
| materials | TEXT[] | |
| status | VARCHAR(50) | 'active', 'inactive', 'draft', 'expired' |
| category_id | BIGINT | Etsy taxonomy ID |
| section_id | BIGINT | |
| has_variations | BOOLEAN DEFAULT false | |
| shipping_profile_id | BIGINT | |
| return_policy_id | BIGINT | |
| is_personalizable | BOOLEAN DEFAULT false | |
| personalization_instructions | TEXT | |
| weight_value | DECIMAL(8,3) | |
| weight_unit | VARCHAR(10) | 'oz', 'g', etc |
| length_value | DECIMAL(8,3) | |
| width_value | DECIMAL(8,3) | |
| height_value | DECIMAL(8,3) | |
| dimension_unit | VARCHAR(10) | |
| etsy_created_at | TIMESTAMP | |
| etsy_updated_at | TIMESTAMP | |
| synced_at | TIMESTAMP | |
| created_at | TIMESTAMP | |
| updated_at | TIMESTAMP | |

Indexes: `etsy_listing_id`, `etsy_shop_id`, `status`, `title` (full-text)

---

## listing_images

| Column | Type | Notes |
|---|---|---|
| id | UUID PK | |
| listing_id | UUID FK → listings.id CASCADE | |
| etsy_image_id | BIGINT | |
| url_fullxfull | TEXT | |
| url_570xN | TEXT | |
| alt_text | TEXT | |
| rank | INTEGER | position order |
| created_at | TIMESTAMP | |

---

## listing_variations

| Column | Type | Notes |
|---|---|---|
| id | UUID PK | |
| listing_id | UUID FK → listings.id CASCADE | |
| etsy_product_id | BIGINT | |
| property_name | VARCHAR(255) | e.g. 'Size', 'Color' |
| value | VARCHAR(255) | |
| price | DECIMAL(10,2) | |
| quantity | INTEGER | |
| sku | VARCHAR(255) | |
| is_available | BOOLEAN DEFAULT true | |
| created_at | TIMESTAMP | |

---

## bulk_edit_sessions (Sprint 7 — IMPLEMENTED)

| Column | Type | Notes |
|---|---|---|
| id | VARCHAR(36) PK | UUID stored as string |
| organization_id | VARCHAR(36) FK → organizations.id CASCADE | indexed |
| created_by_user_id | VARCHAR(36) FK → users.id SET NULL | nullable |
| name | VARCHAR(255) | optional session label |
| status | VARCHAR(50) DEFAULT 'draft' | 'draft', 'preview_ready', 'canceled' ('applied' in Sprint 8) |
| selected_listing_ids | JSON NOT NULL | array of listing UUID strings |
| selected_count | INTEGER DEFAULT 0 | denormalized count |
| change_count | INTEGER DEFAULT 0 | denormalized count |
| preview_generated_at | TIMESTAMP WITH TIME ZONE | nullable |
| applied_at | TIMESTAMP WITH TIME ZONE | nullable (Sprint 8) |
| canceled_at | TIMESTAMP WITH TIME ZONE | nullable |
| created_at | TIMESTAMP WITH TIME ZONE | |
| updated_at | TIMESTAMP WITH TIME ZONE | |

---

## bulk_edit_changes (Sprint 7 — IMPLEMENTED)

| Column | Type | Notes |
|---|---|---|
| id | VARCHAR(36) PK | UUID stored as string |
| bulk_edit_session_id | VARCHAR(36) FK → bulk_edit_sessions.id CASCADE | indexed |
| listing_id | VARCHAR(36) FK → listings.id SET NULL | nullable — session-level change, not per-listing |
| field_name | VARCHAR(100) NOT NULL | e.g. 'title', 'price_amount', 'tags' |
| operation | VARCHAR(50) NOT NULL | set/append/prepend/replace/add_tag/remove_tag/percentage_change/fixed_amount_change |
| old_value | JSON | nullable — snapshot of value before add (informational) |
| new_value | JSON | nullable — computed at apply time |
| operation_value | JSON NOT NULL | the rule value (e.g. " | Summer Sale" for append) |
| validation_status | VARCHAR(20) DEFAULT 'pending' | 'pending', 'valid', 'warning', 'invalid' |
| validation_message | TEXT | nullable |
| created_at | TIMESTAMP WITH TIME ZONE | |
| updated_at | TIMESTAMP WITH TIME ZONE | |

---

## bulk_edit_preview_items (Sprint 7 — IMPLEMENTED)

| Column | Type | Notes |
|---|---|---|
| id | VARCHAR(36) PK | UUID stored as string |
| bulk_edit_session_id | VARCHAR(36) FK → bulk_edit_sessions.id CASCADE | |
| listing_id | VARCHAR(36) FK → listings.id CASCADE | |
| listing_title | TEXT | denormalized — title at preview time |
| before_data | JSON NOT NULL | full editable field snapshot before changes |
| after_data | JSON NOT NULL | full editable field snapshot after all changes applied |
| diff | JSON NOT NULL | `{field: {before: v, after: v}}` for changed fields only |
| validation_status | VARCHAR(20) NOT NULL | 'valid', 'warning', 'invalid' |
| validation_messages | JSON | array of message strings, nullable |
| created_at | TIMESTAMP WITH TIME ZONE | |
| updated_at | TIMESTAMP WITH TIME ZONE | |

Unique constraint: `(bulk_edit_session_id, listing_id)` — upsert on preview regeneration

---

## listing_snapshots

| Column | Type | Notes |
|---|---|---|
| id | UUID PK | |
| listing_id | UUID FK → listings.id | |
| bulk_edit_session_id | UUID FK → bulk_edit_sessions.id | nullable |
| snapshot_data | JSONB NOT NULL | full listing JSON |
| created_at | TIMESTAMP | |

---

## revert_logs

| Column | Type | Notes |
|---|---|---|
| id | UUID PK | |
| organization_id | UUID FK → organizations.id | |
| snapshot_id | UUID FK → listing_snapshots.id | |
| reverted_by | UUID FK → users.id | |
| fields_reverted | TEXT[] | specific fields or ['all'] |
| status | VARCHAR(50) DEFAULT 'pending' | |
| completed_at | TIMESTAMP | |
| created_at | TIMESTAMP | |

---

## media_assets

| Column | Type | Notes |
|---|---|---|
| id | UUID PK | |
| organization_id | UUID FK → organizations.id | |
| filename | VARCHAR(500) | |
| s3_key | TEXT NOT NULL | |
| content_type | VARCHAR(100) | |
| file_size | BIGINT | bytes |
| width | INTEGER | for images |
| height | INTEGER | for images |
| duration_seconds | INTEGER | for videos |
| alt_text | TEXT | |
| created_at | TIMESTAMP | |

---

## audit_logs

| Column | Type | Notes |
|---|---|---|
| id | UUID PK | |
| organization_id | UUID FK → organizations.id | |
| user_id | UUID FK → users.id | nullable (system actions) |
| action | VARCHAR(100) NOT NULL | e.g. 'bulk_edit.apply', 'listing.revert' |
| resource_type | VARCHAR(100) | 'listing', 'subscription', etc |
| resource_id | VARCHAR(255) | |
| metadata | JSONB | |
| ip_address | INET | |
| created_at | TIMESTAMP | |

Index: `organization_id`, `action`, `created_at`

---

## scheduled_jobs

| Column | Type | Notes |
|---|---|---|
| id | UUID PK | |
| organization_id | UUID FK → organizations.id | |
| created_by | UUID FK → users.id | |
| job_type | VARCHAR(100) | 'sync', 'bulk_edit', etc |
| cron_expression | VARCHAR(100) | |
| next_run_at | TIMESTAMP | |
| last_run_at | TIMESTAMP | |
| last_run_status | VARCHAR(50) | |
| is_active | BOOLEAN DEFAULT true | |
| payload | JSONB | |
| created_at | TIMESTAMP | |
| updated_at | TIMESTAMP | |

---

## csv_jobs

| Column | Type | Notes |
|---|---|---|
| id | UUID PK | |
| organization_id | UUID FK → organizations.id | |
| job_type | VARCHAR(20) | 'import', 'export' |
| status | VARCHAR(50) DEFAULT 'pending' | |
| s3_key | TEXT | |
| row_count | INTEGER | |
| error_count | INTEGER | |
| errors | JSONB | |
| completed_at | TIMESTAMP | |
| created_at | TIMESTAMP | |
