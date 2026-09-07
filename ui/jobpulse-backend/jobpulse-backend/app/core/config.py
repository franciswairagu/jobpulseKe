import os
from functools import lru_cache


def _bool(value: str | None, default: bool = False) -> bool:
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


class Settings:
    # --- Database / cache ---
    DATABASE_URL: str = os.getenv("DATABASE_URL", "postgresql+psycopg2://jobpulse:jobpulse@localhost:5432/jobpulse")
    REDIS_URL: str = os.getenv("REDIS_URL", "redis://localhost:6379/0")

    # --- Auth ---
    SECRET_KEY: str = os.getenv("SECRET_KEY", "change-me-in-.env")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))
    REFRESH_TOKEN_EXPIRE_DAYS: int = int(os.getenv("REFRESH_TOKEN_EXPIRE_DAYS", "7"))
    JWT_ALGORITHM: str = os.getenv("JWT_ALGORITHM", "HS256")

    # --- Storage ---
    STORAGE_PROVIDER: str = os.getenv("STORAGE_PROVIDER", "local")  # "local" or "s3"
    STORAGE_BUCKET: str = os.getenv("STORAGE_BUCKET", "")
    LOCAL_STORAGE_DIR: str = os.getenv("LOCAL_STORAGE_DIR", "./data/uploads")
    MAX_CV_UPLOAD_MB: int = int(os.getenv("MAX_CV_UPLOAD_MB", "10"))

    # --- ML model paths (loaded lazily, missing files degrade gracefully) ---
    CV_CATEGORY_MODEL_PATH: str = os.getenv("CV_CATEGORY_MODEL_PATH", "./data/models/tech_category_classifier.joblib")
    MODEL_DEVICE: str = os.getenv("MODEL_DEVICE", "cpu")

    # --- Job data ingestion ---
    JOB_DATASET_PATH: str = os.getenv("JOB_DATASET_PATH", "./data/processed/jobpulse_cleaned.parquet")

    # --- Misc ---
    ENVIRONMENT: str = os.getenv("ENVIRONMENT", "development")
    CORS_ORIGINS: list[str] = [o.strip() for o in os.getenv("CORS_ORIGINS", "http://localhost:5173").split(",") if o.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
