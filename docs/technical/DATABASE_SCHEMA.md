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

## subscriptions

| Column | Type | Notes |
|---|---|---|
| id | UUID PK | |
| organization_id | UUID FK → organizations.id | |
| stripe_customer_id | VARCHAR(255) | |
| stripe_subscription_id | VARCHAR(255) | |
| plan | VARCHAR(50) DEFAULT 'free' | 'free', 'pro_monthly', 'pro_yearly' |
| status | VARCHAR(50) DEFAULT 'active' | 'active', 'canceled', 'past_due', 'trialing' |
| current_period_start | TIMESTAMP | |
| current_period_end | TIMESTAMP | |
| created_at | TIMESTAMP | |
| updated_at | TIMESTAMP | |

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

## bulk_edit_sessions

| Column | Type | Notes |
|---|---|---|
| id | UUID PK | |
| organization_id | UUID FK → organizations.id | |
| created_by | UUID FK → users.id | |
| status | VARCHAR(50) DEFAULT 'draft' | 'draft', 'previewing', 'applying', 'complete', 'failed' |
| total_listings | INTEGER DEFAULT 0 | |
| applied_count | INTEGER DEFAULT 0 | |
| failed_count | INTEGER DEFAULT 0 | |
| completed_at | TIMESTAMP | |
| created_at | TIMESTAMP | |
| updated_at | TIMESTAMP | |

---

## bulk_edit_changes

| Column | Type | Notes |
|---|---|---|
| id | UUID PK | |
| session_id | UUID FK → bulk_edit_sessions.id CASCADE | |
| listing_id | UUID FK → listings.id | |
| field_name | VARCHAR(100) | e.g. 'title', 'price', 'tags' |
| old_value | JSONB | |
| new_value | JSONB | |
| status | VARCHAR(50) DEFAULT 'pending' | 'pending', 'applied', 'failed', 'skipped' |
| error_message | TEXT | |
| applied_at | TIMESTAMP | |
| created_at | TIMESTAMP | |

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
