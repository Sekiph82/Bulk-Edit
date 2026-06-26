import uuid
from sqlalchemy import String, Integer, JSON, ForeignKey, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base, TimestampMixin


class CSVRow(Base, TimestampMixin):
    __tablename__ = "csv_rows"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    organization_id: Mapped[str] = mapped_column(String(36), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    csv_job_id: Mapped[str] = mapped_column(String(36), ForeignKey("csv_jobs.id", ondelete="CASCADE"), nullable=False, index=True)
    row_number: Mapped[int] = mapped_column(Integer, nullable=False)
    listing_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("listings.id", ondelete="SET NULL"), nullable=True, index=True)
    etsy_listing_id: Mapped[str | None] = mapped_column(String(50), nullable=True)
    raw_data: Mapped[object] = mapped_column(JSON, nullable=False)
    normalized_data: Mapped[object] = mapped_column(JSON, nullable=True)
    diff: Mapped[object] = mapped_column(JSON, nullable=True)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="invalid", index=True)
    validation_errors: Mapped[object] = mapped_column(JSON, nullable=True)
    validation_warnings: Mapped[object] = mapped_column(JSON, nullable=True)
    listing_title: Mapped[str | None] = mapped_column(Text, nullable=True)

    job: Mapped["CSVJob"] = relationship("CSVJob", back_populates="rows")
