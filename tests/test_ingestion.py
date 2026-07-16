"""Ingestion: local connector, chunker, idempotent upsert (SPEC-003)."""

from aiboarding.connectors.local import LocalConnector
from aiboarding.ingestion.chunker import chunk_document
from aiboarding.ingestion.pipeline import run_ingestion
from aiboarding.models import SourceDocument
from tests.conftest import SAMPLE_DOCS


def test_local_connector_reads_markdown():
    docs = list(LocalConnector(SAMPLE_DOCS).fetch())
    assert len(docs) >= 3
    titles = {d.title for d in docs}
    assert any("handbook" in t.lower() for t in titles)
    for d in docs:
        assert d.source == "local"
        assert d.content.strip()
        assert d.doc_id


def test_local_connector_not_configured_for_missing_dir():
    assert not LocalConnector("/nonexistent/path/xyz").is_configured()


def test_chunker_splits_and_overlaps():
    long_text = "\n\n".join(f"Paragraph {i} " + ("lorem ipsum " * 30) for i in range(10))
    doc = SourceDocument.create(source="local", title="t", uri="/x", content=long_text)
    chunks = chunk_document(doc)
    assert len(chunks) > 1
    assert all(c.chunk_id == f"{doc.doc_id}:{i}" for i, c in enumerate(chunks))
    assert all(len(c.text) <= 1200 * 2 for c in chunks)


def test_ingestion_is_idempotent(store):
    results1 = run_ingestion([LocalConnector(SAMPLE_DOCS)], store)
    count1 = store.count_chunks()
    run_ingestion([LocalConnector(SAMPLE_DOCS)], store)
    assert store.count_chunks() == count1
    assert results1[0].documents == store.count_documents()


def test_unconfigured_connector_is_skipped(store):
    results = run_ingestion([LocalConnector("/nope")], store)
    assert results[0].skipped is True
    assert store.count_chunks() == 0
