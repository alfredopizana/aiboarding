"""Agent graph: routing, citations, audit trail (SPEC-004)."""

from aiboarding.agent.nodes import classify_intent_heuristic
from aiboarding.models import UserProfile


def test_intent_heuristics():
    assert classify_intent_heuristic("Generate my 90 day plan") == "plan"
    assert classify_intent_heuristic("¿Quién sabe de kubernetes?") == "connect"
    assert classify_intent_heuristic("Where can I find the incident runbook docs?") == "docs"
    assert classify_intent_heuristic("How does billing work?") is None


def test_question_flow_with_citations(agent):
    result = agent.run("How do I set up my development environment?")
    assert result["intent"] == "question"
    assert result["answer"]
    assert result["citations"], "answers must carry citations (SPEC-004 §5)"
    assert all(c.uri for c in result["citations"])


def test_connect_flow_suggests_people(agent):
    result = agent.run("Who should I talk to about kubernetes and incidents?")
    assert result["intent"] == "connect"
    assert result["people_matches"]
    assert "María Gómez" in result["answer"]


def test_plan_flow_generates_plan(agent):
    result = agent.run(
        "Generate my 90 day success plan",
        user=UserProfile(name="Ana", role="engineer", team="platform"),
    )
    assert result["intent"] == "plan"
    assert result["plan"] is not None
    assert len(result["plan"].phases) == 3
    assert "Days 1-30" in result["answer"]


def test_docs_flow_refers_documentation(agent):
    result = agent.run("Where is the documentation about code review?")
    assert result["intent"] == "docs"
    assert result["citations"]
    assert "http" in result["answer"] or "/" in result["answer"]


def test_audit_trail_written(agent):
    result = agent.run("How does on-call work?")
    events = agent.audit.read(result["thread_id"])
    nodes = [e.node for e in events]
    assert nodes[0] == "graph_start"
    assert nodes[-1] == "graph_end"
    assert "classify_intent" in nodes
    assert "finalize" in nodes
    ok_events = [e for e in events if e.status == "ok"]
    assert all(e.latency_ms >= 0 for e in ok_events)


def test_audit_stores_digests_not_raw_prompts(agent):
    query = "How does on-call work at this company exactly?"
    result = agent.run(query)
    events = agent.audit.read(result["thread_id"])
    for e in events:
        assert query not in str(e.model_dump()), "audit must store digests, not raw text"


def test_empty_store_answers_honestly(people, audit, tmp_path):
    from aiboarding.agent.graph import OnboardingAgent
    from aiboarding.agent.llm import FakeLLM
    from aiboarding.agent.nodes import Nodes
    from aiboarding.knowledge.embeddings import HashingEmbedder
    from aiboarding.knowledge.vectorstore import VectorStore
    from aiboarding.plans.generator import PlanGenerator

    store = VectorStore(tmp_path / "empty", HashingEmbedder())
    llm = FakeLLM()
    nodes = Nodes(store, people, llm, audit, PlanGenerator(store, people, llm))
    agent = OnboardingAgent(nodes, audit)
    result = agent.run("How does billing reconciliation work?")
    assert "couldn't find" in result["answer"].lower() or "ingest" in result["answer"].lower()
