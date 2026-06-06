"""ORM models. Vector columns are fixed at 512 dims (CLIP ViT-B/32)."""

import enum
from datetime import datetime, timezone

from pgvector.sqlalchemy import Vector
from sqlalchemy import DateTime, Enum, Float, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

EMBED_DIM = 512  # ViT-B/32 output dim — keep literal, pgvector needs it fixed


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class BatchStatus(str, enum.Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class Decision(str, enum.Enum):
    ACCEPTED = "ACCEPTED"
    REJECTED = "REJECTED"


class Profile(Base):
    __tablename__ = "profiles"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str] = mapped_column(Text, default="", nullable=False)
    threshold_score: Mapped[float] = mapped_column(Float, default=0.55, nullable=False)
    # {"method": "...", "proto_lo": float, "proto_hi": float, "ref_scores": [...]}
    calibration: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    built_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=_utcnow, nullable=False
    )

    concepts: Mapped[list["Concept"]] = relationship(
        back_populates="profile", cascade="all, delete-orphan", order_by="Concept.id"
    )
    reference_images: Mapped[list["ReferenceImage"]] = relationship(
        back_populates="profile", cascade="all, delete-orphan", order_by="ReferenceImage.id"
    )
    batches: Mapped[list["ScreeningBatch"]] = relationship(
        back_populates="profile", cascade="all, delete-orphan"
    )


class Concept(Base):
    __tablename__ = "concepts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    profile_id: Mapped[int] = mapped_column(
        ForeignKey("profiles.id", ondelete="CASCADE"), index=True, nullable=False
    )
    text_description: Mapped[str] = mapped_column(String(300), nullable=False)
    weight: Mapped[float] = mapped_column(Float, default=3.0, nullable=False)  # importance 1-5
    text_embedding: Mapped[list[float] | None] = mapped_column(Vector(EMBED_DIM), nullable=True)

    profile: Mapped[Profile] = relationship(back_populates="concepts")


class ReferenceImage(Base):
    __tablename__ = "reference_images"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    profile_id: Mapped[int] = mapped_column(
        ForeignKey("profiles.id", ondelete="CASCADE"), index=True, nullable=False
    )
    image_url: Mapped[str] = mapped_column(String(500), nullable=False)
    image_embedding: Mapped[list[float] | None] = mapped_column(Vector(EMBED_DIM), nullable=True)

    profile: Mapped[Profile] = relationship(back_populates="reference_images")


class ScreeningBatch(Base):
    __tablename__ = "screening_batches"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    profile_id: Mapped[int] = mapped_column(
        ForeignKey("profiles.id", ondelete="CASCADE"), index=True, nullable=False
    )
    status: Mapped[BatchStatus] = mapped_column(
        Enum(BatchStatus, name="batch_status", values_callable=lambda e: [m.value for m in e]),
        default=BatchStatus.PENDING,
        nullable=False,
    )
    total_images: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    processed: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    error: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=_utcnow, nullable=False
    )

    profile: Mapped[Profile] = relationship(back_populates="batches")
    results: Mapped[list["VerificationResult"]] = relationship(
        back_populates="batch", cascade="all, delete-orphan", order_by="VerificationResult.id"
    )


class VerificationResult(Base):
    __tablename__ = "verification_results"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    batch_id: Mapped[int] = mapped_column(
        ForeignKey("screening_batches.id", ondelete="CASCADE"), index=True, nullable=False
    )
    image_url: Mapped[str] = mapped_column(String(500), nullable=False)
    final_decision: Mapped[Decision] = mapped_column(
        Enum(Decision, name="decision", values_callable=lambda e: [m.value for m in e]),
        nullable=False,
    )
    confidence_score: Mapped[float] = mapped_column(Float, nullable=False)
    reject_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    # {"concept_score": f, "prototype_score": f|null, "coverage": f,
    #  "concepts": [{"concept", "weight", "probability", "present"}, ...]}
    concept_scores: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)

    batch: Mapped[ScreeningBatch] = relationship(back_populates="results")
