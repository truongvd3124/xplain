"""Data access for profiles, concepts and reference images."""

import numpy as np
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.db.models import Concept, Profile, ReferenceImage


class ProfileRepo:
    def __init__(self, db: Session) -> None:
        self.db = db

    # --- profiles ---------------------------------------------------------
    def create(self, name: str, description: str, threshold_score: float,
               concepts: list[dict]) -> Profile:
        profile = Profile(name=name, description=description,
                          threshold_score=threshold_score)
        for c in concepts:
            profile.concepts.append(
                Concept(text_description=c["concept"], weight=float(c["importance"]))
            )
        self.db.add(profile)
        self.db.commit()
        self.db.refresh(profile)
        return profile

    def get(self, profile_id: int) -> Profile | None:
        return self.db.scalar(
            select(Profile)
            .options(selectinload(Profile.concepts),
                     selectinload(Profile.reference_images))
            .where(Profile.id == profile_id)
            # refresh collections even when the instance is already in the
            # session's identity map (e.g. re-read right after an insert)
            .execution_options(populate_existing=True)
        )

    def list_all(self) -> list[Profile]:
        return list(self.db.scalars(
            select(Profile)
            .options(selectinload(Profile.concepts),
                     selectinload(Profile.reference_images))
            .order_by(Profile.created_at.desc())
        ))

    def delete(self, profile: Profile) -> None:
        self.db.delete(profile)
        self.db.commit()

    # --- embeddings -------------------------------------------------------
    def set_concept_embeddings(self, concepts: list[Concept],
                               embeddings: np.ndarray) -> None:
        for concept, emb in zip(concepts, embeddings):
            concept.text_embedding = emb

    def add_reference_image(self, profile_id: int, image_url: str,
                            embedding: np.ndarray) -> ReferenceImage:
        ref = ReferenceImage(profile_id=profile_id, image_url=image_url,
                             image_embedding=embedding)
        self.db.add(ref)
        return ref

    def commit(self) -> None:
        self.db.commit()
