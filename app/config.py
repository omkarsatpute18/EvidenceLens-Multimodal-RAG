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
            mock_mode=os.getenv("MOCK_MODE", "true").lower() in {"1", "true", "yes"},
        )


@lru_cache
def get_settings() -> Settings:
    return Settings.from_env()
