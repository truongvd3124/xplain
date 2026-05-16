from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

BACKEND_DIR = Path(__file__).resolve().parent.parent


class Settings(BaseSettings):
    CLIP_BACKBONE: str = "ViT-B/32"
    DATA_DIR: Path = BACKEND_DIR / "data"

    GEMINI_API_KEY: str = ""
    GEMINI_MODEL: str = "gemini-2.0-flash"

    # --- Verification scoring ---
    # score = CONCEPT_WEIGHT * concept_score + (1 - CONCEPT_WEIGHT) * proto_score
    CONCEPT_WEIGHT: float = 0.5
    # A concept counts as "present" when its probability >= this.
    PRESENCE_THRESHOLD: float = 0.5
    # Best profile must reach this blended score, else "no match".
    MATCH_THRESHOLD: float = 0.5

    ALLOWED_ORIGINS: list[str] = [
        "http://localhost:5173",
        "http://localhost:3000",
    ]

    model_config = SettingsConfigDict(
        env_file=BACKEND_DIR / ".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


settings = Settings()
