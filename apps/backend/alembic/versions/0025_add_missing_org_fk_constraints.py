"""add missing ON DELETE CASCADE foreign keys on organization_id

Nine tables had organization_id declared as a plain column with no foreign
key constraint at all (found during owner-review validation of the
Etsy-compliance branch, via a real-Postgres test of DELETE /api/v1/auth/me:
account deletion silently left orphaned Etsy shop/token/listing rows behind
because there was no DB-level mechanism to cascade-delete them). This
migration adds the same ForeignKey(..., ondelete="CASCADE") convention
already used by every other org-scoped table in the schema (see DECISIONS.md
2026-06-25: "All foreign keys must have ON DELETE behavior defined").

If this migration fails with a foreign key violation, it means at least one
row in the affected table has an organization_id that does not match any
row in organizations — that is pre-existing orphaned data unrelated to this
migration, and must be cleaned up or reassigned before this migration can
apply. Do not weaken this migration to work around orphaned data silently.

Revision ID: 0025
Revises: 0024
Create Date: 2026-07-13

"""
from alembic import op

revision = "0025"
down_revision = "0024"
branch_labels = None
depends_on = None

TABLES = [
    "etsy_oauth_states",
    "etsy_shops",
    "listings",
    "cost_profiles",
    "listing_costs",
    "social_connections",
    "social_oauth_states",
    "sync_jobs",
    "video_renders",
]


def upgrade() -> None:
    for table in TABLES:
        op.create_foreign_key(
            f"fk_{table}_organization_id",
            table,
            "organizations",
            ["organization_id"],
            ["id"],
            ondelete="CASCADE",
        )


def downgrade() -> None:
    for table in TABLES:
        op.drop_constraint(f"fk_{table}_organization_id", table, type_="foreignkey")
