"""Connector registry."""

from __future__ import annotations

from aiboarding.config import Settings
from aiboarding.connectors.base import Connector
from aiboarding.connectors.confluence import ConfluenceConnector
from aiboarding.connectors.gdrive import GDriveConnector
from aiboarding.connectors.github import GitHubConnector
from aiboarding.connectors.local import LocalConnector

__all__ = [
    "Connector",
    "LocalConnector",
    "ConfluenceConnector",
    "GDriveConnector",
    "GitHubConnector",
    "build_connectors",
    "REAL_SOURCES",
]

# Real, external knowledge sources. `local` (data/sample_docs) is a demo/offline
# fixture whose content is typically also in Confluence/GitHub, so it is excluded
# from "all" to avoid duplicate documents; ingest it explicitly with --source local.
REAL_SOURCES = ("confluence", "gdrive", "github")


def build_connectors(settings: Settings, local_path: str | None = None) -> dict[str, Connector]:
    return {
        "local": LocalConnector(local_path or settings.data_dir / "sample_docs"),
        "confluence": ConfluenceConnector(
            settings.confluence_base_url, settings.confluence_email, settings.confluence_api_token
        ),
        "gdrive": GDriveConnector(settings.gdrive_credentials_path, settings.gdrive_folder_list),
        "github": GitHubConnector(settings.github_token, settings.github_repo_list),
    }
