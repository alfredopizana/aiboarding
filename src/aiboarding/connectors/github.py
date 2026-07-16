"""GitHub connector: README + markdown docs from configured repos (SPEC-003 §2.4)."""

from __future__ import annotations

import base64
import logging
from collections.abc import Iterable

import httpx

from aiboarding.connectors.base import Connector
from aiboarding.models import SourceDocument

logger = logging.getLogger(__name__)

API = "https://api.github.com"
DOC_EXTENSIONS = (".md", ".mdx", ".rst", ".txt")


class GitHubConnector(Connector):
    name = "github"

    def __init__(self, token: str, repos: list[str]):
        self.token = token
        self.repos = repos

    def is_configured(self) -> bool:
        return bool(self.token and self.repos)

    def _headers(self) -> dict:
        return {
            "Authorization": f"Bearer {self.token}",
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
        }

    def _doc_paths(self, client: httpx.Client, repo: str) -> list[str]:
        meta = client.get(f"{API}/repos/{repo}", headers=self._headers())
        meta.raise_for_status()
        branch = meta.json().get("default_branch", "main")
        tree = client.get(
            f"{API}/repos/{repo}/git/trees/{branch}?recursive=1", headers=self._headers()
        )
        tree.raise_for_status()
        paths = []
        for node in tree.json().get("tree", []):
            p = node.get("path", "")
            if node.get("type") != "blob" or not p.lower().endswith(DOC_EXTENSIONS):
                continue
            if p.lower().startswith(("docs/", "doc/")) or "/" not in p:
                paths.append(p)
        return paths

    def fetch(self) -> Iterable[SourceDocument]:
        with httpx.Client(timeout=30) as client:
            for repo in self.repos:
                try:
                    paths = self._doc_paths(client, repo)
                except httpx.HTTPError as exc:
                    logger.warning("GitHub repo %s failed: %s", repo, exc)
                    continue
                for path in paths:
                    resp = client.get(
                        f"{API}/repos/{repo}/contents/{path}", headers=self._headers()
                    )
                    if resp.status_code != 200:
                        continue
                    payload = resp.json()
                    if payload.get("encoding") == "base64":
                        content = base64.b64decode(payload["content"]).decode(
                            "utf-8", errors="replace"
                        )
                    else:
                        content = payload.get("content", "")
                    if not content.strip():
                        continue
                    yield SourceDocument.create(
                        source="github",
                        title=f"{repo}/{path}",
                        uri=f"https://github.com/{repo}/blob/HEAD/{path}",
                        content=content,
                        repo=repo,
                        path=path,
                    )
