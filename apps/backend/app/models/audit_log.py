import uuid
from sqlalchemy import String, Text, ForeignKey, JSON
from sqlalchemy.orm import mapped_column, Mapped
from app.db.base import Base, TimestampMixin


class AuditLog(Base, TimestampMixin):
    __tablename__ = "audit_logs"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    organization_id: Mapped[str] = mapped_column(String(36), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    event_type: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    entity_type: Mapped[str | None] = mapped_column(String(100), nullable=True)
    entity_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    message: Mapped[str | None] = mapped_column(Text, nullable=True)
    extra_data: Mapped[object | None] = mapped_column(JSON, nullable=True, name="metadata")

    # M06.04 per-item write audit trail — indexed for the required filters
    # (job id, listing id via entity_id, field, result status, revert
    # status, date range via created_at). Before/after values and any other
    # detail stay in extra_data above rather than duplicating columns for
    # data that isn't filtered on directly.
    apply_job_id: Mapped[str | None] = mapped_column(String(36), nullable=True, index=True)
    revert_job_id: Mapped[str | None] = mapped_column(String(36), nullable=True, index=True)
    field_name: Mapped[str | None] = mapped_column(String(100), nullable=True, index=True)
    result_status: Mapped[str | None] = mapped_column(String(20), nullable=True, index=True)
    revert_status: Mapped[str | None] = mapped_column(String(50), nullable=True, index=True)
