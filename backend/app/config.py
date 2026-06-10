from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field
from functools import lru_cache


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Application
    app_name: str = "AI Society Intelligence Platform"
    app_version: str = "1.0.0"
    environment: str = Field(default="development")
    debug: bool = Field(default=False)

    # Security
    secret_key: str = Field(default="change-this-secret-key-in-production")
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 60
    refresh_token_expire_days: int = 7

    # Database
    database_url: str = Field(
        default="postgresql+asyncpg://asip_user:asip_password@localhost:5432/asip_db"
    )

    # ChromaDB
    chroma_host: str = Field(default="localhost")
    chroma_port: int = Field(default=8001)
    chroma_collection_name: str = Field(default="asip_knowledge_base")

    # LLM
    llm_provider: str = Field(default="openai")  # openai | google
    llm_model: str = Field(default="gpt-4o")
    openai_api_key: str = Field(default="")
    google_api_key: str = Field(default="")
    gemini_model: str = Field(default="gemini-1.5-pro")
    embedding_model: str = Field(default="text-embedding-3-small")

    # Notifications
    sendgrid_api_key: str = Field(default="")
    sendgrid_from_email: str = Field(default="noreply@asip.ai")
    twilio_account_sid: str = Field(default="")
    twilio_auth_token: str = Field(default="")
    twilio_from_number: str = Field(default="")

    @property
    def is_development(self) -> bool:
        return self.environment == "development"

    @property
    def is_production(self) -> bool:
        return self.environment == "production"


@lru_cache()
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
