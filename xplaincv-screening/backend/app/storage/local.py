"""Local-disk image storage.

Files are stored under DATA_DIR and exposed by FastAPI static mounts:
  refs/<profile_id>/<uuid>.<ext>     -> /refs/...      (reference images)
  uploads/<batch_id>/<uuid>.<ext>    -> /uploads/...   (batch images)

The DB stores the public URL (e.g. "/uploads/3/ab12.jpg"); `path_for()` maps
it back to the filesystem. Swap this module for an S3 backend in production.
"""

import io
import uuid
from pathlib import Path

from PIL import Image, UnidentifiedImageError

from app.config import settings

ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp", ".bmp", ".avif"}


class InvalidImageError(ValueError):
    pass


def _validated_ext(filename: str | None, data: bytes) -> str:
    ext = Path(filename or "").suffix.lower()
    if ext not in ALLOWED_EXTENSIONS:
        ext = ".jpg"
    try:
        Image.open(io.BytesIO(data)).verify()
    except (UnidentifiedImageError, OSError) as exc:
        raise InvalidImageError(f"not a readable image: {filename}") from exc
    return ext


def save_reference_image(profile_id: int, filename: str | None, data: bytes) -> str:
    return _save(settings.REF_DIR / str(profile_id), f"/refs/{profile_id}", filename, data)


def save_batch_image(batch_id: int, filename: str | None, data: bytes) -> str:
    return _save(settings.UPLOAD_DIR / str(batch_id), f"/uploads/{batch_id}", filename, data)


def _save(directory: Path, url_prefix: str, filename: str | None, data: bytes) -> str:
    ext = _validated_ext(filename, data)
    directory.mkdir(parents=True, exist_ok=True)
    name = f"{uuid.uuid4().hex[:12]}{ext}"
    (directory / name).write_bytes(data)
    return f"{url_prefix}/{name}"


def path_for(image_url: str) -> Path:
    """Map a stored public URL back to its file on disk."""
    rel = image_url.lstrip("/")
    if rel.startswith("refs/"):
        return settings.REF_DIR / rel[len("refs/"):]
    if rel.startswith("uploads/"):
        return settings.UPLOAD_DIR / rel[len("uploads/"):]
    raise ValueError(f"unrecognised image url: {image_url}")


def open_rgb(image_url: str) -> Image.Image:
    return Image.open(path_for(image_url)).convert("RGB")
