"""Confluence Cloud connector via REST API v2 (SPEC-003 §2.2)."""

from __future__ import annotations

import logging
import re
from collections.abc import Iterable

import httpx

from aiboarding.connectors.base import Connector
from aiboarding.models import SourceDocument

logger = logging.getLogger(__name__)

_TAG_RE = re.compile(r"<[^>]+>")
_WS_RE = re.compile(r"\n{3,}")


def strip_html(html: str) -> str:
    text = html.replace("</p>", "\n\n").replace("<br/>", "\n").replace("<br>", "\n")
    text = re.sub(r"</h[1-6]>", "\n\n", text)
    text = re.sub(r"</li>", "\n", text)
    text = _TAG_RE.sub("", text)
    return _WS_RE.sub("\n\n", text).strip()


class ConfluenceConnector(Connector):
    name = "confluence"

    def __init__(self, base_url: str, email: str, api_token: str):
        self.base_url = base_url.rstrip("/")
        self.email = email
        self.api_token = api_token

    def is_configured(self) -> bool:
        return bool(self.base_url and self.email and self.api_token)

    def fetch(self) -> Iterable[SourceDocument]:
        auth = (self.email, self.api_token)
        url = f"{self.base_url}/api/v2/pages"
        params: dict = {"body-format": "storage", "limit": 50}
        with httpx.Client(timeout=30) as client:
            while url:
                resp = client.get(url, params=params, auth=auth)
                resp.raise_for_status()
                data = resp.json()
                # Site base for building real page URLs (e.g. ".../wiki").
                site_base = (data.get("_links") or {}).get("base") or self.base_url
                for page in data.get("results", []):
                    body = (page.get("body", {}).get("storage", {}) or {}).get("value", "")
                    content = strip_html(body)
                    if not content:
                        continue
                    # webui is the real browser path: /spaces/<KEY>/pages/<id>/<slug>.
                    webui = (page.get("_links") or {}).get("webui")
                    page_uri = (
                        f"{site_base}{webui}" if webui else f"{self.base_url}/pages/{page['id']}"
                    )
                    yield SourceDocument.create(
                        source="confluence",
                        title=page.get("title", f"Page {page['id']}"),
                        uri=page_uri,
                        content=content,
                        space_id=str(page.get("spaceId", "")),
                        page_id=str(page["id"]),
                    )
                next_link = (data.get("_links") or {}).get("next")
                url = f"{self.base_url.split('/wiki')[0]}{next_link}" if next_link else None
                params = {}
