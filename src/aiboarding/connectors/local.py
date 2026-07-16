"""Local filesystem connector: .md, .txt, .pdf (SPEC-003 §2.1)."""

from __future__ import annotations

import logging
from collections.abc import Iterable
from pathlib import Path

from aiboarding.connectors.base import Connector
from aiboarding.models import SourceDocument

logger = logging.getLogger(__name__)

SUPPORTED = {".md", ".txt", ".pdf"}


def _read_pdf(path: Path) -> str:
    from pypdf import PdfReader

    reader = PdfReader(str(path))
    return "\n\n".join((page.extract_text() or "") for page in reader.pages)


class LocalConnector(Connector):
    name = "local"

    def __init__(self, docs_dir: str | Path):
        self.docs_dir = Path(docs_dir).expanduser().resolve()

    def is_configured(self) -> bool:
        return self.docs_dir.is_dir()

    def fetch(self) -> Iterable[SourceDocument]:
        for path in sorted(self.docs_dir.rglob("*")):
            if not path.is_file() or path.suffix.lower() not in SUPPORTED:
                continue
            try:
                if path.suffix.lower() == ".pdf":
                    content = _read_pdf(path)
                else:
                    content = path.read_text(encoding="utf-8", errors="replace")
            except Exception as exc:  # noqa: BLE001
                logger.warning("Skipping %s: %s", path, exc)
                continue
            if not content.strip():
                continue
            yield SourceDocument.create(
                source="local",
                title=path.stem.replace("_", " ").replace("-", " ").strip(),
                uri=str(path),
                content=content,
                mime=path.suffix.lower().lstrip("."),
            )
