"""add per-item write audit trail columns to audit_logs

M06.04: extends the existing, already-general-purpose `audit_logs` table
(already used for apply/revert/media/variation job start/finish events)
with the columns needed to give it a searchable per-item write trail
without duplicating it into a new table. `apply_job_id`/`revert_job_id`/
`field_name`/`result_status`/`revert_status` are the fields this task's
required filters (job id, listing id, field, result status, revert status,
date range) need as real indexed columns; before/after values and any other
detail stay in the existing `metadata` (extra_data) JSON column, which was
already flexible enough for that. See DECISIONS.md.

Revision ID: 0027
Revises: 0026
Create Date: 2026-08-31

"""
import sqlalchemy as sa
from alembic import op

revision = "0027"
down_revision = "0026"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("audit_logs", sa.Column("apply_job_id", sa.String(36), nullable=True))
    op.add_column("audit_logs", sa.Column("revert_job_id", sa.String(36), nullable=True))
    op.add_column("audit_logs", sa.Column("field_name", sa.String(100), nullable=True))
    op.add_column("audit_logs", sa.Column("result_status", sa.String(20), nullable=True))
    op.add_column("audit_logs", sa.Column("revert_status", sa.String(50), nullable=True))
    op.create_index("ix_audit_logs_apply_job_id", "audit_logs", ["apply_job_id"])
    op.create_index("ix_audit_logs_revert_job_id", "audit_logs", ["revert_job_id"])
    op.create_index("ix_audit_logs_field_name", "audit_logs", ["field_name"])
    op.create_index("ix_audit_logs_result_status", "audit_logs", ["result_status"])
    op.create_index("ix_audit_logs_revert_status", "audit_logs", ["revert_status"])


def downgrade() -> None:
    op.drop_index("ix_audit_logs_revert_status", table_name="audit_logs")
    op.drop_index("ix_audit_logs_result_status", table_name="audit_logs")
    op.drop_index("ix_audit_logs_field_name", table_name="audit_logs")
    op.drop_index("ix_audit_logs_revert_job_id", table_name="audit_logs")
    op.drop_index("ix_audit_logs_apply_job_id", table_name="audit_logs")
    op.drop_column("audit_logs", "revert_status")
    op.drop_column("audit_logs", "result_status")
    op.drop_column("audit_logs", "field_name")
    op.drop_column("audit_logs", "revert_job_id")
    op.drop_column("audit_logs", "apply_job_id")
