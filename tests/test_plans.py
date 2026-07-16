"""90-day plan generator (SPEC-005)."""

from aiboarding.agent.llm import FakeLLM
from aiboarding.models import UserProfile
from aiboarding.plans.generator import PlanGenerator


def _gen(populated_store, people):
    return PlanGenerator(populated_store, people, FakeLLM())


def test_plan_has_three_phases(populated_store, people):
    plan = _gen(populated_store, people).generate(UserProfile(name="Ana", role="engineer"))
    assert [p.name for p in plan.phases] == ["Days 1-30", "Days 31-60", "Days 61-90"]
    for phase in plan.phases:
        assert phase.objective
        assert len(phase.items) >= 3


def test_relationship_items_reference_real_people(populated_store, people):
    plan = _gen(populated_store, people).generate(
        UserProfile(name="Ana", role="engineer", team="platform")
    )
    rel_items = [i for p in plan.phases for i in p.items if i.category == "relationships"]
    assert rel_items
    known_names = {p.name for p in people.people}
    assert any(set(i.suggested_contacts) & known_names for i in rel_items)


def test_learning_items_reference_real_docs(populated_store, people):
    plan = _gen(populated_store, people).generate(UserProfile(name="Ana", role="engineer"))
    docs = [d for p in plan.phases for i in p.items for d in i.suggested_docs]
    assert docs, "learning items should link ingested docs"


def test_unknown_role_falls_back_to_default(populated_store, people):
    plan = _gen(populated_store, people).generate(UserProfile(name="X", role="astronaut"))
    assert len(plan.phases) == 3


def test_markdown_rendering(populated_store, people):
    plan = _gen(populated_store, people).generate(
        UserProfile(name="Ana", role="product", team="product", start_date="2026-08-01")
    )
    md = plan.to_markdown()
    assert "# 90-Day Success Plan — Ana" in md
    assert "## Days 1-30" in md
    assert "2026-08-01" in md
