from pathlib import Path

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    ZCBM_ROOT: Path = Path("/home/ubuntu/zcbm")
    BACKBONE: str = "ViT-B/32"
    CONCEPT_INDEX: str = "index/all_ViT-B32_index.bin"
    METADATA_PATH: str = "concept_bank/all.txt"
    CLASSNAMES_DIR: str = "data/classnames"
    NUM_CONCEPT_CANDIDATES: int = 2048
    NUM_PRESENT_CONCEPTS: int = 16
    LASSO_ALPHA: float = 1e-5
    UPLOAD_DIR: Path = Path(__file__).resolve().parent.parent / "uploads"
    DATABASE_URL: str = "sqlite:///./xplaincv.db"
    ALLOWED_ORIGINS: list[str] = ["http://localhost:5173", "http://localhost:3000"]

    model_config = {"env_prefix": "XPLAINCV_"}


settings = Settings()
