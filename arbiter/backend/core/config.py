"""
config.py — Centralised settings management for Arbiter backend.
All environment variables are loaded here. Nothing else should read os.environ directly.
"""
from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field


class Settings(BaseSettings):
    """Application settings loaded from environment variables / .env file."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # ── Google Gemini ────────────────────────────────────────────────────────
    gemini_api_key: str = Field(..., description="Google Gemini API key from AI Studio")
    gemini_model: str = Field(default="gemini-2.0-pro-exp", description="Gemini model ID")

    # ── Google Cloud ─────────────────────────────────────────────────────────
    google_cloud_project: str = Field(..., description="GCP project ID")
    google_cloud_region: str = Field(default="asia-south1", description="GCP region")
    gcs_bucket_name: str = Field(default="arbiter-documents", description="GCS bucket for PDFs")
    vertex_ai_search_id: str = Field(default="", description="Vertex AI Search data store ID")

    # ── Firebase ─────────────────────────────────────────────────────────────
    firebase_project_id: str = Field(..., description="Firebase project ID")
    firebase_service_account_path: str = Field(
        default="", description="Path to service account JSON (empty = use ADC)"
    )

    # ── Razorpay ─────────────────────────────────────────────────────────────
    razorpay_key_id: str = Field(..., description="Razorpay API key ID")
    razorpay_key_secret: str = Field(..., description="Razorpay API key secret")
    razorpay_webhook_secret: str = Field(default="", description="Razorpay webhook signature secret")

    # ── App ───────────────────────────────────────────────────────────────────
    environment: str = Field(default="development", description="development | staging | production")
    log_level: str = Field(default="INFO", description="Logging level")
    cors_origins: list[str] = Field(
        default=["http://localhost:3000"],
        description="Allowed CORS origins",
    )
    doc_price_paise: int = Field(default=29900, description="Per-document price in paise (₹299)")
    monthly_price_paise: int = Field(default=79900, description="Monthly plan price in paise (₹799)")

    # ── Sentry (crash alerting) ───────────────────────────────────────────────
    sentry_dsn: str = Field(default="", description="Sentry DSN for crash reporting (empty = disabled)")

    # ── Admin API ─────────────────────────────────────────────────────────────
    admin_secret_key: str = Field(default="change-me-in-production", description="X-Admin-Key header for /api/admin endpoints")

    # ── Backup ────────────────────────────────────────────────────────────────
    backup_bucket_name: str = Field(default="arbiter-backups", description="GCS bucket for Firestore backups")

    # ── Rate Limiting ─────────────────────────────────────────────────────────
    rate_limit_per_minute: int = Field(default=60, description="Max requests per minute per IP")
    rate_limit_per_day: int = Field(default=500, description="Max requests per day per IP")

    @property
    def is_production(self) -> bool:
        """True when running in production."""
        return self.environment == "production"

    @property
    def is_development(self) -> bool:
        """True when running locally."""
        return self.environment == "development"


@lru_cache
def get_settings() -> Settings:
    """Return cached Settings instance. Use this everywhere."""
    return Settings()


# Module-level singleton for convenience imports
settings = get_settings()
