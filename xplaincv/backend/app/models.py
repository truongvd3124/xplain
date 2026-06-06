from datetime import datetime, timezone

from sqlalchemy import Float, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class Classification(Base):
    __tablename__ = "classifications"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    created_at: Mapped[str] = mapped_column(
        String, default=lambda: datetime.now(timezone.utc).isoformat()
    )
    mode: Mapped[str] = mapped_column(String(20))
    image_filename: Mapped[str] = mapped_column(String(255))
    original_filename: Mapped[str] = mapped_column(String(255))
    predicted_class: Mapped[str] = mapped_column(String(255))
    confidence: Mapped[float] = mapped_column(Float)
    feat_gap: Mapped[float] = mapped_column(Float)
    result_json: Mapped[str] = mapped_column(Text)
    inference_time_ms: Mapped[int] = mapped_column(Integer)
