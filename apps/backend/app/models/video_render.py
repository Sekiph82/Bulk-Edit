import uuid
import json
from sqlalchemy import String, Text, Integer, Float, Boolean, DateTime
from sqlalchemy.orm import Mapped, mapped_column
from app.db.base import Base, TimestampMixin


class VideoRender(Base, TimestampMixin):
    __tablename__ = "video_renders"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    organization_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True)
    template_id: Mapped[str] = mapped_column(String(100), nullable=False)
    # status: pending | rendering | completed | failed
    status: Mapped[str] = mapped_column(String(50), nullable=False, default="pending", index=True)
    image_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    aspect_ratio: Mapped[str | None] = mapped_column(String(10), nullable=True)
    duration_seconds: Mapped[float | None] = mapped_column(Float, nullable=True)
    file_size_bytes: Mapped[int | None] = mapped_column(Integer, nullable=True)
    width: Mapped[int | None] = mapped_column(Integer, nullable=True)
    height: Mapped[int | None] = mapped_column(Integer, nullable=True)
    is_etsy_ready: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    # JSON list of issue strings; None means not yet checked
    etsy_issues_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    # file_path is server-side only — never returned in API responses
    file_path: Mapped[str | None] = mapped_column(Text, nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    completed_at: Mapped[object] = mapped_column(DateTime(timezone=True), nullable=True)

    def get_etsy_issues(self) -> list[str]:
        if self.etsy_issues_json is None:
            return []
        try:
            return json.loads(self.etsy_issues_json)
        except (ValueError, TypeError):
            return []
