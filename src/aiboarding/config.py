"""Application settings (SPEC-002 §2). Loaded from environment / .env."""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # LLM
    llm_provider: str = "fake"  # openai | fake
    llm_model: str = "gpt-4o-mini"
    openai_api_key: str = ""
    embeddings_provider: str = "hashing"  # openai | hashing

    # Storage
    data_dir: Path = Path("./data")
    vectorstore_dir: Path = Path("./data/vectorstore")
    audit_dir: Path = Path("./data/audit")
    people_file: Path = Path("./data/people.yaml")

    # Persistence (users, plans, progress)
    progress_backend: str = "sqlite"  # sqlite | firebase (future)
    db_path: Path = Path("./data/aiboarding.db")
    # When set (e.g. Railway injects DATABASE_URL), Postgres backs BOTH the
    # relational store and the vector store (pgvector) — the app becomes stateless.
    database_url: str = ""

    # Tracing (LangSmith)
    langsmith_tracing: bool = False
    langsmith_api_key: str = ""
    langsmith_project: str = "aiboarding"

    # UI
    show_audit_button: bool = True  # show a "Ver auditoría" button under chat answers
    ui_password: str = ""  # if set, the Streamlit app requires this password (shared/hosted use)

    # Confluence
    confluence_base_url: str = ""
    confluence_email: str = ""
    confluence_api_token: str = ""

    # GitHub
    github_token: str = ""
    github_repos: str = ""  # csv org/repo

    # Google Drive
    gdrive_credentials_path: str = ""
    gdrive_folder_ids: str = ""

    # Phase 2
    slack_bot_token: str = ""
    slack_app_token: str = ""
    smtp_host: str = ""
    smtp_port: int = 587
    smtp_user: str = ""
    smtp_password: str = ""
    email_from: str = "onboarding-bot@company.com"

    @property
    def github_repo_list(self) -> list[str]:
        return [r.strip() for r in self.github_repos.split(",") if r.strip()]

    @property
    def gdrive_folder_list(self) -> list[str]:
        return [f.strip() for f in self.gdrive_folder_ids.split(",") if f.strip()]


class _EnvAliasSettings(Settings):
    """Accept both AIBOARDING_-prefixed and legacy env names."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        env_prefix="AIBOARDING_",
    )


@lru_cache
def get_settings() -> Settings:
    prefixed = _EnvAliasSettings()
    plain = Settings()
    # Start from the unprefixed/legacy values, then let any AIBOARDING_-prefixed
    # values win. `model_fields_set` captures exactly the fields the prefixed
    # source provided — whether from OS env vars OR the .env file (os.environ
    # alone misses .env-only values).
    merged = plain.model_dump()
    for field in prefixed.model_fields_set:
        merged[field] = getattr(prefixed, field)
    return Settings(**merged)


def reset_settings_cache() -> None:
    get_settings.cache_clear()
