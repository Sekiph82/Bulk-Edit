from sqlalchemy import String, DateTime, Text
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import Uuid
from app.db.base import Base
import uuid


class EtsyOAuthState(Base):
    __tablename__ = "etsy_oauth_states"

    id: Mapped[str] = mapped_column(Uuid(as_uuid=False), primary_key=True, default=lambda: str(uuid.uuid4()))
    state: Mapped[str] = mapped_column(String(128), unique=True, nullable=False, index=True)
    code_verifier: Mapped[str] = mapped_column(Text, nullable=False)
    organization_id: Mapped[str] = mapped_column(Uuid(as_uuid=False), nullable=False)
    user_id: Mapped[str] = mapped_column(Uuid(as_uuid=False), nullable=False)
    expires_at: Mapped[object] = mapped_column(DateTime(timezone=True), nullable=False)
    consumed_at: Mapped[object] = mapped_column(DateTime(timezone=True), nullable=True)
