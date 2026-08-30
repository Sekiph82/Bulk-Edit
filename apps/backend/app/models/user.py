import uuid
from sqlalchemy import String, Boolean
from sqlalchemy.orm import mapped_column, Mapped, relationship

from app.db.base import Base, TimestampMixin


class User(Base, TimestampMixin):
    __tablename__ = "users"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    full_name: Mapped[str] = mapped_column(String(255), nullable=False, default="")
    first_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    last_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    is_verified: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    is_superuser: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    # passive_deletes=True on both: same fix as Organization.members — let
    # PostgreSQL's ON DELETE CASCADE (both organization_members.user_id and
    # refresh_tokens.user_id) handle child-row deletion instead of letting
    # SQLAlchemy attempt to NULL out those NOT NULL columns when the User is
    # deleted. Found via a real-Postgres test of DELETE /api/v1/auth/me.
    memberships: Mapped[list["OrganizationMember"]] = relationship("OrganizationMember", back_populates="user", lazy="select", passive_deletes=True)
    refresh_tokens: Mapped[list["RefreshToken"]] = relationship("RefreshToken", back_populates="user", lazy="select", passive_deletes=True)

    @property
    def display_name(self) -> str:
        """Deterministic fallback chain: first+last -> first -> last -> email -> "Account"."""
        first = (self.first_name or "").strip()
        last = (self.last_name or "").strip()
        if first and last:
            return f"{first} {last}"
        if first:
            return first
        if last:
            return last
        if self.email:
            return self.email
        return "Account"
