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
    from aiboarding.plans.generator import PlanGenerator

    settings = Settings(
        llm_provider="fake",
        embeddings_provider="hashing",
        vectorstore_dir=tmp_path / "vs",
        audit_dir=tmp_path / "audit",
    )
    llm = FakeLLM()
    plan_gen = PlanGenerator(populated_store, people, llm)
    nodes = Nodes(populated_store, people, llm, audit, plan_gen)
    agent = OnboardingAgent(nodes, audit)
    svc = Services(settings, populated_store, people, llm, audit, plan_gen, agent)
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
