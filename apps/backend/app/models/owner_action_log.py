import uuid
from datetime import datetime
from sqlalchemy import String, Text, DateTime, ForeignKey
from sqlalchemy.orm import mapped_column, Mapped
from app.db.base import Base


class OwnerActionLog(Base):
    """Audit trail for owner-console actions (plan changes, comp grants,
    refunds, manual sync, password reset requests, alert rule changes).

    Deliberately separate from the per-organization AuditLog model: several
    owner actions (alert rule CRUD, password reset requests) aren't
    naturally scoped to one organization, and AuditLog.organization_id is
    NOT NULL. Both organization_id and target_user_id here are optional so
    an action can target either, both, or neither."""
    __tablename__ = "owner_action_logs"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    actor_user_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    organization_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("organizations.id", ondelete="SET NULL"), nullable=True, index=True)
    target_user_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    action_type: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    message: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
