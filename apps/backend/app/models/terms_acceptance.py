import uuid
from sqlalchemy import String, ForeignKey
from sqlalchemy.orm import mapped_column, Mapped
from app.db.base import Base, TimestampMixin


class TermsAcceptance(Base, TimestampMixin):
    """One row per acceptance event. created_at (via TimestampMixin) doubles
    as terms_accepted_at — acceptance is recorded at the moment it happens,
    never backdated or inferred."""

    __tablename__ = "terms_acceptances"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    terms_version: Mapped[str] = mapped_column(String(50), nullable=False)
    privacy_version: Mapped[str] = mapped_column(String(50), nullable=False)
    acceptance_source: Mapped[str] = mapped_column(String(50), nullable=False, default="web_registration")
