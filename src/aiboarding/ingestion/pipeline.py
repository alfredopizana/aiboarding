"""Ingestion pipeline: connectors → chunker → vector store (SPEC-003)."""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass

from aiboarding.connectors.base import Connector
from aiboarding.ingestion.chunker import chunk_document
from aiboarding.knowledge.vectorstore import VectorStore
from aiboarding.models import Source, SourceDocument

logger = logging.getLogger(__name__)


@dataclass
class IngestResult:
    connector: str
    documents: int
    chunks: int
    skipped: bool = False


def run_ingestion(connectors: list[Connector], store: VectorStore) -> list[IngestResult]:
    results: list[IngestResult] = []
    for connector in connectors:
        if not connector.is_configured():
            logger.warning("Connector '%s' not configured — skipping.", connector.name)
            results.append(IngestResult(connector.name, 0, 0, skipped=True))
            continue
        docs = 0
        chunks = 0
        for doc in connector.fetch():
            doc_chunks = chunk_document(doc)
            store.upsert_document(doc.doc_id, doc_chunks)
            docs += 1
            chunks += len(doc_chunks)
        store.persist()
        logger.info("Ingested %d docs (%d chunks) from %s", docs, chunks, connector.name)
        results.append(IngestResult(connector.name, docs, chunks))
    return results


def _slugify(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-") or "untitled"


def ingest_text(
    store: VectorStore,
    title: str,
    content: str,
    uri: str = "",
    source: Source = "manual",
    **metadata,
) -> tuple[SourceDocument, int]:
    """Ingest a single pushed document (API/CLI), no connector needed.

    The doc_id derives from (source, uri), so pushing the same uri again
    updates the document in place. Returns (document, chunk_count).
    """
    uri = uri or f"manual://{_slugify(title)}"
    doc = SourceDocument.create(source=source, title=title, uri=uri, content=content, **metadata)
    chunks = chunk_document(doc)
    store.upsert_document(doc.doc_id, chunks)
    store.persist()
    logger.info("Ingested pushed doc '%s' (%d chunks) as %s", title, len(chunks), doc.doc_id)
    return doc, len(chunks)
