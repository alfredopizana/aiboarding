"""People directory: who to connect with, by topic/expertise (SPEC-002 §2)."""

from __future__ import annotations

import re
from pathlib import Path

import yaml

from aiboarding.models import Person, PersonMatch

_TOKEN_RE = re.compile(r"[a-záéíóúñü0-9]+", re.IGNORECASE)


class PeopleDirectory:
    def __init__(self, people: list[Person]):
        self.people = people

    @classmethod
    def from_yaml(cls, path: str | Path) -> PeopleDirectory:
        path = Path(path)
        if not path.exists():
            return cls([])
        data = yaml.safe_load(path.read_text()) or {}
        return cls([Person(**p) for p in data.get("people", [])])

    def upsert(self, person: Person) -> bool:
        """Insert or replace by id. Returns True if the person is new."""
        for i, existing in enumerate(self.people):
            if existing.id == person.id:
                self.people[i] = person
                return False
        self.people.append(person)
        return True

    def save(self, path: str | Path) -> None:
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        payload = {"people": [p.model_dump() for p in self.people]}
        path.write_text(yaml.safe_dump(payload, sort_keys=False, allow_unicode=True))

    def match(self, topic: str, team: str = "", limit: int = 3) -> list[PersonMatch]:
        tokens = set(_TOKEN_RE.findall(topic.lower()))
        matches: list[PersonMatch] = []
        for person in self.people:
            score = 0.0
            reasons: list[str] = []
            for exp in person.expertise:
                exp_tokens = set(_TOKEN_RE.findall(exp.lower()))
                overlap = tokens & exp_tokens
                if overlap:
                    score += 2.0 * len(overlap)
                    reasons.append(f"expertise: {exp}")
            role_tokens = set(_TOKEN_RE.findall(person.role.lower()))
            if tokens & role_tokens:
                score += 1.0
                reasons.append(f"role: {person.role}")
            if team and person.team.lower() == team.lower():
                score += 1.5
                reasons.append(f"same team ({person.team})")
            if person.onboarding_buddy:
                score += 0.5
                reasons.append("onboarding buddy")
            if score > 0:
                matches.append(
                    PersonMatch(person=person, score=round(score, 2), reason="; ".join(reasons))
                )
        matches.sort(key=lambda m: m.score, reverse=True)
        return matches[:limit]

    def by_team(self, team: str) -> list[Person]:
        return [p for p in self.people if p.team.lower() == team.lower()]

    def buddies(self) -> list[Person]:
        return [p for p in self.people if p.onboarding_buddy]
