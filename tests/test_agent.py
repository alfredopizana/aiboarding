"""Agent graph: routing, citations, audit trail (SPEC-004)."""

from aiboarding.agent.nodes import classify_intent_heuristic
from aiboarding.models import UserProfile


def test_intent_heuristics():
    assert classify_intent_heuristic("Generate my 90 day plan") == "plan"
    assert classify_intent_heuristic("¿Quién sabe de kubernetes?") == "connect"
    assert classify_intent_heuristic("Where can I find the incident runbook docs?") == "docs"
    assert classify_intent_heuristic("How does billing work?") is None


def test_advice_questions_route_to_reasoning_not_docs():
    # Advice/recommendation questions must reason, even if they mention "docs".
    assert (
        classify_intent_heuristic(
            "¿Qué me recomiendas que haga primero, leer la documentación o agendar reuniones?"
        )
        == "question"
    )
    assert classify_intent_heuristic("Should I read the docs first or ship a task?") == "question"


def test_plan_and_repo_context_feed_the_answer(populated_store, people, audit, tmp_path):
    from aiboarding.agent.llm import FakeLLM
    from aiboarding.agent.nodes import Nodes
    from aiboarding.models import UserProfile
    from aiboarding.persistence import get_progress_store
    from aiboarding.plans.generator import PlanGenerator

    progress = get_progress_store("sqlite", tmp_path / "p.db")
    gen = PlanGenerator(populated_store, people, FakeLLM())
    user = UserProfile(name="Ada", team="data", email="ada@x.dev")
    su = progress.upsert_user(user, user.email)
    progress.save_plan(su.id, gen.generate(user))

    nodes = Nodes(
        populated_store, people, FakeLLM(), audit, gen,
        progress=progress, repos=["Noesis-Foundry/core-api"],
    )
    assert "90-DAY PLAN" in nodes._plan_context(user)
    assert "Noesis-Foundry/core-api" in nodes._profile_context(user)
    # answer_question now surfaces relevant teammates alongside the answer
    out = nodes.answer_question({"thread_id": "t", "query": "incident response", "user": user})
    assert "people_matches" in out


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
