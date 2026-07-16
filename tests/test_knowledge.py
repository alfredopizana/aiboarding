"""Knowledge layer: vector store retrieval, persistence, people matching."""

from aiboarding.knowledge.embeddings import HashingEmbedder
from aiboarding.knowledge.vectorstore import VectorStore


def test_retrieve_returns_relevant_chunks(populated_store):
    results = populated_store.retrieve("how do I set up my development environment", k=3)
    assert results
    assert results[0].score > 0
    all_text = " ".join(r.chunk.text.lower() for r in results)
    assert "environment" in all_text or "install" in all_text or "set up" in all_text


def test_retrieve_empty_store(store):
    assert store.retrieve("anything") == []


def test_persistence_roundtrip(populated_store, tmp_path):
    populated_store.persist()
    reloaded = VectorStore(populated_store.directory, HashingEmbedder())
    assert reloaded.count_chunks() == populated_store.count_chunks()
    assert reloaded.retrieve("code review process", k=1)


def test_people_match_by_expertise(people):
    matches = people.match("kubernetes deployment incident")
    assert matches
    assert matches[0].person.id == "maria.gomez"
    assert "expertise" in matches[0].reason


def test_people_match_team_boost(people):
    matches = people.match("roadmap metrics", team="product")
    assert matches[0].person.team == "product"


def test_people_buddies(people):
    assert len(people.buddies()) >= 2
