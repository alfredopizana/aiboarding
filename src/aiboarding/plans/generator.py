"""90-Day Success Plan generator (SPEC-005)."""

from __future__ import annotations

from pathlib import Path

import yaml

from aiboarding.agent.llm import LLMClient
from aiboarding.knowledge.people import PeopleDirectory
from aiboarding.knowledge.vectorstore import VectorStore
from aiboarding.models import PlanItem, PlanPhase, SuccessPlan, UserProfile

TEMPLATES_PATH = Path(__file__).parent / "templates.yaml"

PHASE_NAMES = {"phase1": "Days 1-30", "phase2": "Days 31-60", "phase3": "Days 61-90"}


class PlanGenerator:
    def __init__(
        self,
        store: VectorStore,
        people: PeopleDirectory,
        llm: LLMClient,
        templates_path: str | Path = TEMPLATES_PATH,
    ):
        self.store = store
        self.people = people
        self.llm = llm
        self.templates = yaml.safe_load(Path(templates_path).read_text())

    def generate(self, user: UserProfile) -> SuccessPlan:
        role_templates = self.templates["roles"].get(
            user.role.lower(), self.templates["roles"]["default"]
        )
        objectives = self.templates["phase_objectives"]
        phases: list[PlanPhase] = []
        for phase_key in ("phase1", "phase2", "phase3"):
            items = [
                self._enrich_item(raw, user) for raw in role_templates.get(phase_key, [])
            ]
            phases.append(
                PlanPhase(
                    name=PHASE_NAMES[phase_key],  # type: ignore[arg-type]
                    objective=objectives[phase_key],
                    items=items,
                )
            )
        summary = self._summary(user)
        return SuccessPlan(user=user, phases=phases, summary=summary)

    def _enrich_item(self, raw: dict, user: UserProfile) -> PlanItem:
        """Attach real people and real docs to each template item (SPEC-005 §3.3)."""
        topic = raw.get("topic", raw["title"])
        contacts: list[str] = []
        docs: list[str] = []
        if raw["category"] == "relationships":
            contacts = [m.person.name for m in self.people.match(topic, team=user.team, limit=2)]
            if not contacts:
                contacts = [p.name for p in self.people.buddies()[:2]]
        else:
            matches = self.people.match(topic, team=user.team, limit=1)
            contacts = [m.person.name for m in matches]
        retrieved = self.store.retrieve(topic, k=2, min_score=0.1)
        seen: set[str] = set()
        for r in retrieved:
            if r.chunk.uri not in seen:
                docs.append(r.chunk.uri)
                seen.add(r.chunk.uri)
        return PlanItem(
            title=raw["title"],
            description=raw["description"],
            category=raw["category"],
            suggested_contacts=contacts,
            suggested_docs=docs,
        )

    def _summary(self, user: UserProfile) -> str:
        base = (
            f"This 90-day success plan guides {user.name} ({user.role}"
            + (f", team {user.team}" if user.team else "")
            + ") through three phases: learn & connect (1-30), contribute with support (31-60), "
            "and deliver autonomously (61-90). Items link to real teammates and ingested docs."
        )
        if self.llm.model != "fake":
            try:
                return self.llm.complete(
                    "Write a 2-sentence motivating summary for a 90-day onboarding plan. "
                    "Same language as the user's role/team text if not English.",
                    base,
                )
            except Exception:  # noqa: BLE001
                return base
        return base
