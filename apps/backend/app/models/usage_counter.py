import uuid
from sqlalchemy import String, Integer, ForeignKey, UniqueConstraint
from sqlalchemy.orm import mapped_column, Mapped
from sqlalchemy import Uuid

from app.db.base import Base, TimestampMixin


class UsageCounter(Base, TimestampMixin):
    __tablename__ = "usage_counters"
    __table_args__ = (
        UniqueConstraint("organization_id", "period_key", name="uq_usage_org_period"),
    )

    id: Mapped[str] = mapped_column(Uuid(as_uuid=False), primary_key=True, default=lambda: str(uuid.uuid4()))
    organization_id: Mapped[str] = mapped_column(Uuid(as_uuid=False), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    period_key: Mapped[str] = mapped_column(String(7), nullable=False)
    listings_synced: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    bulk_edits_used: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    ai_credits_used: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    media_assets_used: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
