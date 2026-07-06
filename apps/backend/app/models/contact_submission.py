import uuid
from sqlalchemy import String, Text
from sqlalchemy.orm import mapped_column, Mapped
from app.db.base import Base, TimestampMixin


class ContactSubmission(Base, TimestampMixin):
    __tablename__ = "contact_submissions"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    email: Mapped[str] = mapped_column(String(320), nullable=False, index=True)
    subject: Mapped[str] = mapped_column(String(200), nullable=False)
    message: Mapped[str] = mapped_column(Text, nullable=False)
    # Whether send_contact_notification_email() succeeded at submission time —
    # lets the owner console flag submissions that never actually reached SUPPORT_EMAIL.
    email_delivered: Mapped[bool] = mapped_column(nullable=False, default=False)
