from sqlalchemy import Boolean, String, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import Uuid
from app.db.base import Base, TimestampMixin
import uuid


class EtsyShop(Base, TimestampMixin):
    __tablename__ = "etsy_shops"

    id: Mapped[str] = mapped_column(Uuid(as_uuid=False), primary_key=True, default=lambda: str(uuid.uuid4()))
    organization_id: Mapped[str] = mapped_column(Uuid(as_uuid=False), nullable=False, index=True)
    etsy_shop_id: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    shop_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    is_connected: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    last_synced_at: Mapped[object] = mapped_column(DateTime(timezone=True), nullable=True)

    token: Mapped["EtsyToken"] = relationship("EtsyToken", back_populates="shop", uselist=False, cascade="all, delete-orphan")
