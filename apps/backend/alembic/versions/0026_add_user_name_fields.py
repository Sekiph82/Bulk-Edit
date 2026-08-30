"""add first_name/last_name to users

Adds durable profile name fields so the app can greet users by name instead
of raw email (owner request, 2026-08-30). Nullable — existing users are not
forced to fill them in; the User.display_name property falls back to email
(then "Account") when both are unset. Reuses the existing free-text
`full_name` field's precedent but keeps it untouched (still set at
registration) rather than migrating/deprecating it in this round.

Revision ID: 0026
Revises: 0025
Create Date: 2026-08-30

"""
import sqlalchemy as sa
from alembic import op

revision = "0026"
down_revision = "0025"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("users", sa.Column("first_name", sa.String(255), nullable=True))
    op.add_column("users", sa.Column("last_name", sa.String(255), nullable=True))


def downgrade() -> None:
    op.drop_column("users", "last_name")
    op.drop_column("users", "first_name")
