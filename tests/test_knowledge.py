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


def test_people_directory_covers_new_teams(people):
    teams = {p.team for p in people.people}
    assert {"it", "data", "custom-eng", "devops", "qa", "security", "web"} <= teams


def test_people_upsert_and_save_roundtrip(people, tmp_path):
    from aiboarding.knowledge.people import PeopleDirectory
    from aiboarding.models import Person

    n = len(people.people)
    new = Person(id="test.person", name="Test Person", role="Engineer", team="qa")
    assert people.upsert(new) is True
    updated = Person(id="test.person", name="Test Person", role="Senior Engineer", team="qa")
    assert people.upsert(updated) is False
    assert len(people.people) == n + 1

    out = tmp_path / "people.yaml"
    people.save(out)
    reloaded = PeopleDirectory.from_yaml(out)
    assert len(reloaded.people) == n + 1
    assert any(p.id == "test.person" and p.role == "Senior Engineer" for p in reloaded.people)
