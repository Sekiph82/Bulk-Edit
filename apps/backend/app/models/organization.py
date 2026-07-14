import uuid
from sqlalchemy import String, ForeignKey
from sqlalchemy.orm import mapped_column, Mapped, relationship

from app.db.base import Base, TimestampMixin


class Organization(Base, TimestampMixin):
    __tablename__ = "organizations"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    owner_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id", ondelete="RESTRICT"), nullable=False)

    # passive_deletes=True: let PostgreSQL's ON DELETE CASCADE (declared on
    # OrganizationMember.organization_id) handle child-row deletion. Without
    # this, SQLAlchemy's default relationship behavior tries to NULL out
    # organization_id on already-loaded members when the parent Organization
    # is deleted — which fails with a NOT NULL violation, since that column
    # is NOT NULL. Found via a real-Postgres test of DELETE /api/v1/auth/me
    # (SQLite's default FK enforcement didn't catch this in the test suite).
    members: Mapped[list["OrganizationMember"]] = relationship("OrganizationMember", back_populates="organization", lazy="select", passive_deletes=True)
