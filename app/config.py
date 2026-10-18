from functools import lru_cache
import os
from pathlib import Path

from pydantic import BaseModel, Field


class Settings(BaseModel):
    model_provider: str = "mock"
    model_name: str = "deterministic-evidence-model"
    model_base_url: str = ""
    model_api_key: str = ""
    embedding_model: str = "local-token-overlap"
    vector_store_path: Path = Path("data/evidence.json")
    max_upload_mb: int = Field(default=25, ge=1, le=500)
    top_k: int = Field(default=8, ge=1, le=50)
    model_timeout_seconds: float = Field(default=20.0, gt=0, le=120)
    model_retries: int = Field(default=2, ge=0, le=5)
    model_max_output_chars: int = Field(default=2000, ge=200, le=10000)
    ocr_enabled: bool = False
    ocr_timeout_seconds: float = Field(default=10.0, gt=0, le=60)
    ocr_max_chars: int = Field(default=4000, ge=200, le=20000)
    mock_mode: bool = True

    @classmethod
    def from_env(cls) -> "Settings":
        return cls(
            model_provider=os.getenv("MODEL_PROVIDER", "mock"),
            model_name=os.getenv("MODEL_NAME", "deterministic-evidence-model"),
            model_base_url=os.getenv("MODEL_BASE_URL", ""),
            model_api_key=os.getenv("MODEL_API_KEY", ""),
            embedding_model=os.getenv("EMBEDDING_MODEL", "local-token-overlap"),
            vector_store_path=Path(os.getenv("VECTOR_STORE_PATH", "data/evidence.json")),
            max_upload_mb=int(os.getenv("MAX_UPLOAD_MB", "25")),
            top_k=int(os.getenv("TOP_K", "8")),
            model_timeout_seconds=float(os.getenv("MODEL_TIMEOUT_SECONDS", "20")),
            model_retries=int(os.getenv("MODEL_RETRIES", "2")),
            model_max_output_chars=int(os.getenv("MODEL_MAX_OUTPUT_CHARS", "2000")),
            ocr_enabled=os.getenv("OCR_ENABLED", "false").lower() in {"1", "true", "yes"},
            ocr_timeout_seconds=float(os.getenv("OCR_TIMEOUT_SECONDS", "10")),
            ocr_max_chars=int(os.getenv("OCR_MAX_CHARS", "4000")),
            mock_mode=os.getenv("MOCK_MODE", "true").lower() in {"1", "true", "yes"},
        )


@lru_cache
def get_settings() -> Settings:
    return Settings.from_env()
