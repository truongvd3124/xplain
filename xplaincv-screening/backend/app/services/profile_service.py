"""Profile lifecycle: create -> attach references -> build (embed + calibrate)."""

from dataclasses import dataclass
from datetime import datetime, timezone

import numpy as np

from app.config import settings
from app.db.models import Profile
from app.repositories.profile_repo import ProfileRepo
from app.schemas.concept import ConceptOut
from app.schemas.profile import ProfileCreate, ProfileDetail, ProfileSummary, ReferenceImageOut
from app.services import scoring
from app.services.clip_engine import ClipEngine
from app.storage import local as storage


class ProfileNotFoundError(LookupError):
    pass


class ProfileNotBuiltError(RuntimeError):
    pass


@dataclass
class ProfileBundle:
    """Everything the screening loop needs, loaded once per batch."""

    profile_id: int
    name: str
    threshold_score: float
    concepts: list[dict]                 # [{"concept", "weight"}]
    concept_embeddings: np.ndarray       # (N, 512)
    weights: np.ndarray                  # (N,)
    prototype: np.ndarray | None         # (512,) or None when no references
    proto_lo: float
    proto_hi: float

    @property
    def has_references(self) -> bool:
        return self.prototype is not None


class ProfileService:
    def __init__(self, repo: ProfileRepo, clip: ClipEngine) -> None:
        self.repo = repo
        self.clip = clip

    # --- CRUD ---------------------------------------------------------------
    def create(self, payload: ProfileCreate) -> ProfileDetail:
        profile = self.repo.create(
            name=payload.name,
            description=payload.description,
            threshold_score=settings.DEFAULT_THRESHOLD_SCORE,
            concepts=[c.model_dump() for c in payload.concepts],
        )
        return self.to_detail(profile)

    def get(self, profile_id: int) -> Profile:
        profile = self.repo.get(profile_id)
        if profile is None:
            raise ProfileNotFoundError(f"profile {profile_id} not found")
        return profile

    def list_all(self) -> list[ProfileSummary]:
        return [self.to_summary(p) for p in self.repo.list_all()]

    def delete(self, profile_id: int) -> None:
        self.repo.delete(self.get(profile_id))

    # --- build steps ----------------------------------------------------------
    def add_reference_images(self, profile_id: int,
                             files: list[tuple[str | None, bytes]]) -> ProfileDetail:
        """Store + embed reference images. files = [(filename, bytes), ...]."""
        profile = self.get(profile_id)
        for filename, data in files:
            url = storage.save_reference_image(profile.id, filename, data)
            image = storage.open_rgb(url)
            embedding = self.clip.encode_image(image)
            self.repo.add_reference_image(profile.id, url, embedding)
        self.repo.commit()
        return self.to_detail(self.get(profile_id))

    def build(self, profile_id: int) -> ProfileDetail:
        """Embed concepts, build prototype, calibrate the threshold window."""
        profile = self.get(profile_id)

        concept_texts = [c.text_description for c in profile.concepts]
        embeddings = self.clip.encode_concepts(concept_texts)
        self.repo.set_concept_embeddings(profile.concepts, embeddings)

        weights = np.array([c.weight for c in profile.concepts], dtype=np.float32)
        ref_embeddings = self._ref_matrix(profile)

        calibration = scoring.calibrate(
            embeddings, weights, ref_embeddings,
            self.clip.neutral_embedding, self.clip.logit_scale,
            settings.CONCEPT_WEIGHT,
        )
        profile.calibration = calibration
        profile.threshold_score = self._derive_threshold(calibration)
        profile.built_at = datetime.now(timezone.utc)
        self.repo.commit()
        return self.to_detail(self.get(profile_id))

    @staticmethod
    def _derive_threshold(calibration: dict) -> float:
        """Base threshold from reference self-scores when calibrated.

        With leave-one-out scores available, allow one std below their mean —
        but never below the validated default. Without references, keep the
        default (concept-only profiles have no calibration signal).
        """
        ref_scores = calibration.get("ref_scores") or []
        if len(ref_scores) < 3:
            return settings.DEFAULT_THRESHOLD_SCORE
        arr = np.asarray(ref_scores, dtype=np.float64)
        derived = float(arr.mean() - arr.std())
        return round(max(settings.DEFAULT_THRESHOLD_SCORE, min(derived, 0.85)), 4)

    # --- worker loading ---------------------------------------------------------
    def load_bundle(self, profile_id: int) -> ProfileBundle:
        profile = self.get(profile_id)
        if profile.built_at is None:
            raise ProfileNotBuiltError(
                f"profile {profile_id} has not been built yet"
            )
        concept_embeddings = np.asarray(
            [np.asarray(c.text_embedding, dtype=np.float32) for c in profile.concepts]
        )
        ref_embeddings = self._ref_matrix(profile)
        prototype = (
            scoring.build_prototype(ref_embeddings)
            if ref_embeddings.shape[0] > 0 else None
        )
        calibration = profile.calibration or {}
        return ProfileBundle(
            profile_id=profile.id,
            name=profile.name,
            threshold_score=profile.threshold_score,
            concepts=[
                {"concept": c.text_description, "weight": c.weight}
                for c in profile.concepts
            ],
            concept_embeddings=concept_embeddings,
            weights=np.array([c.weight for c in profile.concepts], dtype=np.float32),
            prototype=prototype,
            proto_lo=float(calibration.get("proto_lo", 0.0)),
            proto_hi=float(calibration.get("proto_hi", 1.0)),
        )

    @staticmethod
    def _ref_matrix(profile: Profile) -> np.ndarray:
        rows = [
            np.asarray(r.image_embedding, dtype=np.float32)
            for r in profile.reference_images
            if r.image_embedding is not None
        ]
        return np.asarray(rows) if rows else np.zeros((0, 512), dtype=np.float32)

    # --- mapping -------------------------------------------------------------
    @staticmethod
    def to_summary(profile: Profile) -> ProfileSummary:
        return ProfileSummary(
            id=profile.id,
            name=profile.name,
            description=profile.description,
            threshold_score=profile.threshold_score,
            num_concepts=len(profile.concepts),
            num_references=len(profile.reference_images),
            is_built=profile.built_at is not None,
            created_at=profile.created_at,
        )

    @classmethod
    def to_detail(cls, profile: Profile) -> ProfileDetail:
        summary = cls.to_summary(profile)
        return ProfileDetail(
            **summary.model_dump(),
            concepts=[
                ConceptOut(
                    id=c.id,
                    concept=c.text_description,
                    importance=int(c.weight),
                    has_embedding=c.text_embedding is not None,
                )
                for c in profile.concepts
            ],
            reference_images=[
                ReferenceImageOut(
                    id=r.id,
                    image_url=r.image_url,
                    has_embedding=r.image_embedding is not None,
                )
                for r in profile.reference_images
            ],
            calibration=profile.calibration,
        )
