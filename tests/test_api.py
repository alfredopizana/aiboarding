"""API endpoints (SPEC-006 §1) — TestClient, fully offline."""

import pytest
from fastapi.testclient import TestClient

from aiboarding.api.server import create_app
from aiboarding.container import Services


@pytest.fixture
def client(populated_store, people, audit, tmp_path):
    from aiboarding.agent.graph import OnboardingAgent
    from aiboarding.agent.llm import FakeLLM
    from aiboarding.agent.nodes import Nodes
    from aiboarding.config import Settings
    from aiboarding.persistence import get_progress_store
    from aiboarding.plans.generator import PlanGenerator

    settings = Settings(
        llm_provider="fake",
        embeddings_provider="hashing",
        vectorstore_dir=tmp_path / "vs",
        audit_dir=tmp_path / "audit",
        people_file=tmp_path / "people.yaml",
        db_path=tmp_path / "aiboarding.db",
    )
    llm = FakeLLM()
    plan_gen = PlanGenerator(populated_store, people, llm)
    nodes = Nodes(populated_store, people, llm, audit, plan_gen)
    agent = OnboardingAgent(nodes, audit)
    progress = get_progress_store("sqlite", settings.db_path)
    svc = Services(settings, populated_store, people, llm, audit, plan_gen, agent, progress)
    return TestClient(create_app(svc))


def test_health(client):
    resp = client.get("/health")
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "ok"
    assert body["docs_indexed"] >= 3
    assert body["people"] >= 5


def test_ask_returns_answer_and_citations(client):
    resp = client.post("/ask", json={"query": "How do I set up my dev environment?"})
    assert resp.status_code == 200
    body = resp.json()
    assert body["answer"]
    assert body["thread_id"].startswith("thr_")
    assert body["citations"]


def test_ask_connect_intent(client):
    resp = client.post("/ask", json={"query": "Who knows about kubernetes?"})
    assert resp.status_code == 200
    assert resp.json()["intent"] == "connect"
    assert resp.json()["people"]


def test_plan_endpoint(client):
    resp = client.post(
        "/plan", json={"name": "Ana", "role": "engineer", "team": "platform"}
    )
    assert resp.status_code == 200
    body = resp.json()
    assert len(body["plan"]["phases"]) == 3
    assert "90-Day Success Plan" in body["markdown"]


def test_people_endpoint(client):
    resp = client.get("/people", params={"topic": "security training"})
    assert resp.status_code == 200
    assert any(m["person"]["id"] == "dev.patel" for m in resp.json())


def test_audit_endpoint_roundtrip(client):
    thread = client.post("/ask", json={"query": "Where are the runbook docs?"}).json()["thread_id"]
    resp = client.get(f"/audit/{thread}")
    assert resp.status_code == 200
    nodes = [e["node"] for e in resp.json()]
    assert "graph_start" in nodes and "graph_end" in nodes


def test_audit_404(client):
    assert client.get("/audit/does-not-exist").status_code == 404


def test_ask_validation_error(client):
    assert client.post("/ask", json={}).status_code == 422


def test_add_document_endpoint(client):
    resp = client.post(
        "/documents",
        json={
            "title": "Office Parking Policy",
            "content": "Visitor parking permits require a blue badge from reception.",
        },
    )
    assert resp.status_code == 201
    body = resp.json()
    assert body["doc_id"]
    assert body["uri"] == "manual://office-parking-policy"
    assert body["source"] == "manual"
    assert body["chunks"] >= 1
    # immediately retrievable through the agent
    ask = client.post(
        "/ask",
        json={"query": "Visitor parking permits require a blue badge from reception."},
    ).json()
    assert any(c["uri"] == "manual://office-parking-policy" for c in ask["citations"])


def test_add_document_same_uri_is_update_not_duplicate(client):
    r1 = client.post("/documents", json={"title": "Pet Policy", "content": "Dogs allowed on Fridays."})
    r2 = client.post("/documents", json={"title": "Pet Policy", "content": "Dogs allowed every day."})
    assert r1.json()["doc_id"] == r2.json()["doc_id"]
    assert r2.json()["docs_indexed"] == r1.json()["docs_indexed"]


def test_add_document_rejects_blank_content(client):
    assert client.post("/documents", json={"title": "x", "content": "   "}).status_code == 422
    assert client.post("/documents", json={"title": "x"}).status_code == 422


def test_add_person_endpoint(client, tmp_path):
    person = {
        "id": "sam.jones",
        "name": "Sam Jones",
        "role": "Platform Engineer",
        "team": "platform",
        "expertise": ["grpc", "profiling"],
    }
    resp = client.post("/people", json=person)
    assert resp.status_code == 201
    assert resp.json()["created"] is True
    # visible in expertise matching immediately
    matches = client.get("/people", params={"topic": "grpc profiling"}).json()
    assert any(m["person"]["id"] == "sam.jones" for m in matches)
    # persisted to the configured people file
    assert "sam.jones" in (tmp_path / "people.yaml").read_text()
    # same id again is an update, not a duplicate
    resp2 = client.post("/people", json={**person, "role": "Staff Platform Engineer"})
    assert resp2.json()["created"] is False
    assert resp2.json()["people_total"] == resp.json()["people_total"]
