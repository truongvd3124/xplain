"""Application settings, loaded from environment / backend/.env."""

from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

_BACKEND_DIR = Path(__file__).resolve().parent.parent


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=_BACKEND_DIR / ".env", env_file_encoding="utf-8", extra="ignore"
    )

    # --- infrastructure -------------------------------------------------
    DATABASE_URL: str = "postgresql+psycopg://xplain:xplain@localhost:5432/xplain"
    REDIS_URL: str = "redis://localhost:6379/0"
    CELERY_BROKER_URL: str = "redis://localhost:6379/1"
    CELERY_RESULT_BACKEND: str = "redis://localhost:6379/2"

    # --- AI --------------------------------------------------------------
    GEMINI_API_KEY: str = ""
    GEMINI_MODEL: str = "gemini-2.0-flash"
    LLM_PROVIDER: str = "gemini"
    CLIP_BACKBONE: str = "ViT-B/32"
    EMBED_DIM: int = 512  # informational; pgvector columns use the literal 512

    # --- storage ---------------------------------------------------------
    DATA_DIR: Path = _BACKEND_DIR / "data"

    # --- scoring (validated defaults ported from xplaincv-mvp) -----------
    CONCEPT_WEIGHT: float = 0.5        # blend: concept vs prototype evidence
    PRESENCE_THRESHOLD: float = 0.5    # concept prob >= this => "present"
    DEFAULT_THRESHOLD_SCORE: float = 0.55  # profile threshold before calibration
    COVERAGE_FLOOR: float = 0.6        # min fraction of concepts present
    MAX_REJECT_REASON_CONCEPTS: int = 3

    # --- predict mode (/api/verify) gate, ported from xplaincv-mvp ----------
    MATCH_THRESHOLD: float = 0.55      # min blended score for the top candidate
    CONCEPT_FLOOR: float = 0.45        # min concept_score to pass the gate
    PROTOTYPE_FLOOR: float = 0.45      # min prototype_score (when refs exist)

    # --- batch processing -------------------------------------------------
    BATCH_CHUNK_PROGRESS: int = 5      # flush progress every N images
    MAX_BATCH_IMAGES: int = 500
    RESULTS_PAGE_SIZE: int = 24

    ALLOWED_ORIGINS: list[str] = [
        "http://localhost:5173",
        "http://localhost:3000",
    ]

    @property
    def UPLOAD_DIR(self) -> Path:
        return self.DATA_DIR / "uploads"

    @property
    def REF_DIR(self) -> Path:
        return self.DATA_DIR / "refs"


settings = Settings()
settings.UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
settings.REF_DIR.mkdir(parents=True, exist_ok=True)
