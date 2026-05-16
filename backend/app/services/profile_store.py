import json
import re
import shutil
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path

import numpy as np

from app.config import settings

_PROFILES_DIR = settings.DATA_DIR / "profiles"


@dataclass
class Profile:
    """In-memory representation of one stored class profile."""

    id: str
    class_name: str
    description: str
    concepts: list[dict]                 # {"concept": str, "importance": 1-5}
    concept_embeddings: np.ndarray       # aligned with `concepts` by row
    prototype: np.ndarray                # zeros if no reference images
    ref_embeddings: np.ndarray           # (num_references, D)
    calibration: dict                    # from verify_service.calibrate()
    created_at: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )

    @property
    def num_references(self) -> int:
        return int(self.ref_embeddings.shape[0])

    def summary(self) -> dict:
        """Lightweight dict for list views (no embeddings)."""
        return {
            "id": self.id,
            "class_name": self.class_name,
            "description": self.description,
            "num_concepts": len(self.concepts),
            "num_references": self.num_references,
            "created_at": self.created_at,
        }

    def detail(self) -> dict:
        return {**self.summary(), "concepts": self.concepts,
                "calibration": self.calibration}


def slugify(name: str) -> str:
    """Turn a class name into a filesystem-safe profile id."""
    slug = re.sub(r"[^a-z0-9]+", "-", name.strip().lower()).strip("-")
    return slug or "profile"


def profile_dir(profile_id: str) -> Path:
    return _PROFILES_DIR / profile_id


def list_profiles() -> list[dict]:
    """Summaries of every stored profile, newest first."""
    if not _PROFILES_DIR.is_dir():
        return []
    summaries = []
    for child in _PROFILES_DIR.iterdir():
        meta = child / "profile.json"
        if meta.is_file():
            summaries.append(json.loads(meta.read_text()))
    summaries.sort(key=lambda m: m.get("created_at", ""), reverse=True)
    return [_meta_to_summary(m) for m in summaries]


def load_profile(profile_id: str) -> Profile:
    """Load a full profile (metadata + embeddings) from disk."""
    folder = profile_dir(profile_id)
    if not (folder / "profile.json").is_file():
        raise FileNotFoundError(f"Profile not found: {profile_id}")

    meta = json.loads((folder / "profile.json").read_text())
    return Profile(
        id=meta["id"],
        class_name=meta["class_name"],
        description=meta["description"],
        concepts=meta["concepts"],
        concept_embeddings=np.load(folder / "concepts.npy"),
        prototype=np.load(folder / "prototype.npy"),
        ref_embeddings=np.load(folder / "refs.npy"),
        calibration=meta["calibration"],
        created_at=meta["created_at"],
    )


def save_profile(profile: Profile, ref_images: list[bytes],
                  ref_extensions: list[str]) -> None:
    """Persist a profile, replacing any existing one with the same id."""
    folder = profile_dir(profile.id)
    if folder.exists():
        shutil.rmtree(folder)
    (folder / "images").mkdir(parents=True)

    np.save(folder / "concepts.npy", profile.concept_embeddings)
    np.save(folder / "prototype.npy", profile.prototype)
    np.save(folder / "refs.npy", profile.ref_embeddings)

    for index, (blob, ext) in enumerate(zip(ref_images, ref_extensions)):
        (folder / "images" / f"ref_{index}{ext}").write_bytes(blob)

    meta = {
        "id": profile.id,
        "class_name": profile.class_name,
        "description": profile.description,
        "concepts": profile.concepts,
        "calibration": profile.calibration,
        "num_references": profile.num_references,
        "created_at": profile.created_at,
    }
    (folder / "profile.json").write_text(json.dumps(meta, indent=2))


def delete_profile(profile_id: str) -> bool:
    """Remove a profile folder. Returns False if it did not exist."""
    folder = profile_dir(profile_id)
    if not folder.is_dir():
        return False
    shutil.rmtree(folder)
    return True


def _meta_to_summary(meta: dict) -> dict:
    return {
        "id": meta["id"],
        "class_name": meta["class_name"],
        "description": meta["description"],
        "num_concepts": len(meta["concepts"]),
        "num_references": meta["num_references"],
        "created_at": meta["created_at"],
    }
