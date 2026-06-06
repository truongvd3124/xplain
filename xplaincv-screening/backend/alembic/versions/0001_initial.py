"""initial schema: profiles, concepts, reference_images, screening_batches, verification_results

Revision ID: 0001
Revises:
Create Date: 2026-06-06

"""
import sqlalchemy as sa
from alembic import op
from pgvector.sqlalchemy import Vector
from sqlalchemy.dialects.postgresql import JSONB

revision = "0001"
down_revision = None
branch_labels = None
depends_on = None

EMBED_DIM = 512  # CLIP ViT-B/32

batch_status = sa.Enum(
    "pending", "processing", "completed", "failed", name="batch_status"
)
decision = sa.Enum("ACCEPTED", "REJECTED", name="decision")


def upgrade() -> None:
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")

    op.create_table(
        "profiles",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("name", sa.String(200), nullable=False),
        sa.Column("description", sa.Text(), nullable=False, server_default=""),
        sa.Column("threshold_score", sa.Float(), nullable=False, server_default="0.55"),
        sa.Column("calibration", JSONB(), nullable=True),
        sa.Column("built_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
    )

    op.create_table(
        "concepts",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "profile_id",
            sa.Integer(),
            sa.ForeignKey("profiles.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("text_description", sa.String(300), nullable=False),
        sa.Column("weight", sa.Float(), nullable=False, server_default="3"),
        sa.Column("text_embedding", Vector(EMBED_DIM), nullable=True),
    )
    op.create_index("ix_concepts_profile_id", "concepts", ["profile_id"])

    op.create_table(
        "reference_images",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "profile_id",
            sa.Integer(),
            sa.ForeignKey("profiles.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("image_url", sa.String(500), nullable=False),
        sa.Column("image_embedding", Vector(EMBED_DIM), nullable=True),
    )
    op.create_index("ix_reference_images_profile_id", "reference_images", ["profile_id"])

    op.create_table(
        "screening_batches",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "profile_id",
            sa.Integer(),
            sa.ForeignKey("profiles.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("status", batch_status, nullable=False, server_default="pending"),
        sa.Column("total_images", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("processed", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("error", sa.Text(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
    )
    op.create_index("ix_screening_batches_profile_id", "screening_batches", ["profile_id"])

    op.create_table(
        "verification_results",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "batch_id",
            sa.Integer(),
            sa.ForeignKey("screening_batches.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("image_url", sa.String(500), nullable=False),
        sa.Column("final_decision", decision, nullable=False),
        sa.Column("confidence_score", sa.Float(), nullable=False),
        sa.Column("reject_reason", sa.Text(), nullable=True),
        sa.Column("concept_scores", JSONB(), nullable=False, server_default="{}"),
    )
    op.create_index("ix_verification_results_batch_id", "verification_results", ["batch_id"])


def downgrade() -> None:
    op.drop_table("verification_results")
    op.drop_table("screening_batches")
    op.drop_table("reference_images")
    op.drop_table("concepts")
    op.drop_table("profiles")
    decision.drop(op.get_bind(), checkfirst=True)
    batch_status.drop(op.get_bind(), checkfirst=True)
