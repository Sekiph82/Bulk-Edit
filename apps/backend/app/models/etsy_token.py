from sqlalchemy import String, Text, DateTime, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import Uuid
from app.db.base import Base, TimestampMixin
import uuid


class EtsyToken(Base, TimestampMixin):
    __tablename__ = "etsy_tokens"

    id: Mapped[str] = mapped_column(Uuid(as_uuid=False), primary_key=True, default=lambda: str(uuid.uuid4()))
    etsy_shop_id: Mapped[str] = mapped_column(Uuid(as_uuid=False), ForeignKey("etsy_shops.id", ondelete="CASCADE"), unique=True, nullable=False)
    access_token_enc: Mapped[str] = mapped_column(Text, nullable=False)
    refresh_token_enc: Mapped[str] = mapped_column(Text, nullable=False)
    expires_at: Mapped[object] = mapped_column(DateTime(timezone=True), nullable=False)
    scopes: Mapped[str | None] = mapped_column(String(500), nullable=True)

    shop: Mapped["EtsyShop"] = relationship("EtsyShop", back_populates="token")
