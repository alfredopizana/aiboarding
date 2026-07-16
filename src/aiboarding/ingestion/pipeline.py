"""Ingestion pipeline: connectors → chunker → vector store (SPEC-003)."""

from __future__ import annotations

import logging
from dataclasses import dataclass

from aiboarding.connectors.base import Connector
from aiboarding.ingestion.chunker import chunk_document
from aiboarding.knowledge.vectorstore import VectorStore

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
