import uuid
from datetime import datetime
from sqlalchemy import String, DateTime, ForeignKey, JSON
from sqlalchemy.orm import mapped_column, Mapped
from sqlalchemy import Uuid

from app.db.base import Base


class BillingEvent(Base):
    __tablename__ = "billing_events"

    id: Mapped[str] = mapped_column(Uuid(as_uuid=False), primary_key=True, default=lambda: str(uuid.uuid4()))
    organization_id: Mapped[str | None] = mapped_column(Uuid(as_uuid=False), ForeignKey("organizations.id", ondelete="SET NULL"), nullable=True)
    stripe_event_id: Mapped[str] = mapped_column(String(255), nullable=False, unique=True, index=True)
    event_type: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    payload: Mapped[dict] = mapped_column(JSON, nullable=False)
    processed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
