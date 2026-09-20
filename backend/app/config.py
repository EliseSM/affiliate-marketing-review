from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # Database (Supabase Postgres, pooled/transaction-mode connection string)
    DATABASE_URL: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/postgres"

    # Supabase Storage
    SUPABASE_URL: str = "https://your-project.supabase.co"
    SUPABASE_SERVICE_ROLE_KEY: str = "changeme"
    SUPABASE_RAW_UPLOADS_BUCKET: str = "raw-uploads"
    SUPABASE_ASSETS_BUCKET: str = "submission-assets"

    # LLM provider (swappable, see app/evaluation/llm_judge/provider_factory.py)
    LLM_PROVIDER: str = "openai"
    LLM_MODEL: str = "gpt-4o"
    OPENAI_API_KEY: str = "changeme"
    LLM_MAX_IMAGES_PER_SUBMISSION: int = 6
    LLM_TIMEOUT_SECONDS: int = 60

    # Background job reconciliation sweep
    RECONCILIATION_SWEEP_INTERVAL_SECONDS: int = 45
    RUN_STALE_THRESHOLD_SECONDS: int = 600

    # CORS
    CORS_ALLOWED_ORIGINS: str = "http://localhost:3000"

    # Upload guardrail. The largest fixture in marketing-test-examples/ is
    # ~5.5KB; this is set far above any realistic single upload (including
    # HTML/email with a few embedded images) while still bounding worst-case
    # request size/cost on a publicly reachable endpoint.
    MAX_UPLOAD_SIZE_BYTES: int = 10 * 1024 * 1024  # 10 MiB

    @property
    def cors_allowed_origins_list(self) -> list[str]:
        return [origin.strip() for origin in self.CORS_ALLOWED_ORIGINS.split(",") if origin.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
