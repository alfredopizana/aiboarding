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
    import os

    prefixed = _EnvAliasSettings()
    plain = Settings()
    # Prefixed values win when explicitly set in the environment.
    merged = plain.model_dump()
    for field in Settings.model_fields:
        env_key = f"AIBOARDING_{field.upper()}"
        if env_key in os.environ:
            merged[field] = getattr(prefixed, field)
    return Settings(**merged)


def reset_settings_cache() -> None:
    get_settings.cache_clear()
