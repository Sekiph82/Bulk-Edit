import uuid
from sqlalchemy import String, Text, DateTime, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column
from app.db.base import Base, TimestampMixin


class SocialConnection(Base, TimestampMixin):
    __tablename__ = "social_connections"
    __table_args__ = (UniqueConstraint("organization_id", "platform", name="uq_social_connections_org_platform"),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    organization_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True)
    # platform: "pinterest" | "instagram"
    platform: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    # access_token_encrypted must never appear in API responses
    access_token_encrypted: Mapped[str] = mapped_column(Text, nullable=False)
    token_type: Mapped[str] = mapped_column(String(50), nullable=False, default="Bearer")
    scope: Mapped[str | None] = mapped_column(Text, nullable=True)
    expires_at: Mapped[object] = mapped_column(DateTime(timezone=True), nullable=True)
