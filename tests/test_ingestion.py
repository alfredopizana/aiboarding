"""Ingestion: local connector, chunker, idempotent upsert, pushed docs (SPEC-003)."""

from aiboarding.connectors.local import LocalConnector
from aiboarding.ingestion.chunker import chunk_document
from aiboarding.ingestion.pipeline import ingest_text, run_ingestion
from aiboarding.knowledge.embeddings import HashingEmbedder
from aiboarding.knowledge.vectorstore import VectorStore
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


def test_local_connector_discovers_nested_docs():
    """Runbooks and practice docs live in subdirectories — rglob must find them."""
    titles = {d.title for d in LocalConnector(SAMPLE_DOCS).fetch()}
    assert len(titles) >= 20
    assert any("runbook" in t.lower() for t in titles)
    assert any("trunk" in t.lower() for t in titles)
    assert any("raci" in t.lower() for t in titles)


def test_ingest_text_pushes_manual_doc(store):
    doc, n_chunks = ingest_text(
        store, title="Q3 Team Update", content="We shipped the churn dashboard this quarter."
    )
    assert doc.source == "manual"
    assert doc.uri == "manual://q3-team-update"
    assert n_chunks >= 1
    assert store.count_documents() == 1
    results = store.retrieve("We shipped the churn dashboard this quarter.", k=1)
    assert results and results[0].chunk.doc_id == doc.doc_id
    # ingest_text persists immediately — a reloaded store sees the doc
    reloaded = VectorStore(store.directory, HashingEmbedder())
    assert reloaded.count_chunks() == store.count_chunks()


def test_ingest_text_same_uri_updates_in_place(store):
    doc1, _ = ingest_text(store, title="Travel Policy", content="Version one of the policy.")
    doc2, _ = ingest_text(store, title="Travel Policy", content="Version two replaces it.")
    assert doc1.doc_id == doc2.doc_id
    assert store.count_documents() == 1
    top = store.retrieve("Version two replaces it.", k=1)[0]
    assert "two" in top.chunk.text
