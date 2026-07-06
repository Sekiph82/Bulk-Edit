import uuid
from datetime import datetime
from sqlalchemy import String, Boolean, Integer, Text, DateTime, ForeignKey
from sqlalchemy.orm import mapped_column, Mapped
from app.db.base import Base, TimestampMixin


class OwnerAlertRule(Base, TimestampMixin):
    """Operational alert threshold, evaluated on-demand via the owner
    console's "Run alert check now" action (no background scheduler exists
    yet in this codebase — see admin.py service docstring). Slack webhook
    is stored Fernet-encrypted and never returned to the frontend."""
    __tablename__ = "owner_alert_rules"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    # event_type: payment_failure | sync_failure_spike | bulk_edit_failures | system_health | ai_failures
    event_type: Mapped[str] = mapped_column(String(50), nullable=False, unique=True, index=True)
    enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    threshold_count: Mapped[int] = mapped_column(Integer, nullable=False, default=5)
    window_minutes: Mapped[int] = mapped_column(Integer, nullable=False, default=60)

    channel_email_enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    channel_email_to: Mapped[str | None] = mapped_column(String(500), nullable=True)  # falls back to SUPPORT_EMAIL if empty

    channel_slack_enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    encrypted_slack_webhook: Mapped[str | None] = mapped_column(Text, nullable=True)  # Fernet-encrypted; never echoed to frontend

    last_triggered_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)  # dedupe within window_minutes
    updated_by_user_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
