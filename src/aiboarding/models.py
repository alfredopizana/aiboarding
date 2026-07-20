"""Domain models (SPEC-002 §2, SPEC-003 §1, SPEC-005 §2)."""

from __future__ import annotations

import hashlib
from datetime import datetime, timezone
from typing import Literal

from pydantic import BaseModel, Field

Source = Literal["local", "confluence", "gdrive", "github", "manual"]


def make_doc_id(source: str, uri: str) -> str:
    return hashlib.sha1(f"{source}:{uri}".encode()).hexdigest()[:16]


def digest(text: str) -> str:
    return hashlib.sha256(text.encode()).hexdigest()[:16]


class SourceDocument(BaseModel):
    doc_id: str
    source: Source
    title: str
    uri: str
    content: str
    metadata: dict = Field(default_factory=dict)

    @classmethod
    def create(cls, source: Source, title: str, uri: str, content: str, **metadata) -> SourceDocument:
        return cls(
            doc_id=make_doc_id(source, uri),
            source=source,
            title=title,
            uri=uri,
            content=content,
            metadata=metadata,
        )


class Chunk(BaseModel):
    chunk_id: str
    doc_id: str
    source: Source
    title: str
    uri: str
    text: str
    position: int


class RetrievedChunk(BaseModel):
    chunk: Chunk
    score: float


class Citation(BaseModel):
    title: str
    uri: str
    source: str
    chunk_id: str
    score: float


class Person(BaseModel):
    id: str
    name: str
    role: str
    team: str
    email: str = ""
    slack: str = ""
    expertise: list[str] = Field(default_factory=list)
    onboarding_buddy: bool = False
    timezone: str = ""


class PersonMatch(BaseModel):
    person: Person
    score: float
    reason: str


class UserProfile(BaseModel):
    name: str = "New Hire"
    role: str = "default"
    team: str = ""
    start_date: str | None = None
    email: str = ""  # identity used to load the user's saved plan/progress


class PlanItem(BaseModel):
    title: str
    description: str
    category: Literal["learning", "relationships", "delivery", "process"]
    suggested_contacts: list[str] = Field(default_factory=list)
    suggested_docs: list[str] = Field(default_factory=list)
    done: bool = False


class PlanPhase(BaseModel):
    name: Literal["Days 1-30", "Days 31-60", "Days 61-90"]
    objective: str
    items: list[PlanItem]


class SuccessPlan(BaseModel):
    user: UserProfile
    generated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    phases: list[PlanPhase]
    summary: str = ""

    def to_markdown(self) -> str:
        lines = [f"# 90-Day Success Plan — {self.user.name}", ""]
        lines.append(f"**Role:** {self.user.role}  ·  **Team:** {self.user.team or '—'}")
        if self.user.start_date:
            lines.append(f"**Start date:** {self.user.start_date}")
        lines += ["", self.summary, ""]
        for phase in self.phases:
            lines.append(f"## {phase.name}")
            lines.append(f"*Objective: {phase.objective}*")
            lines.append("")
            for item in phase.items:
                lines.append(f"- [ ] **{item.title}** ({item.category}) — {item.description}")
                if item.suggested_contacts:
                    lines.append(f"  - 🤝 Talk to: {', '.join(item.suggested_contacts)}")
                if item.suggested_docs:
                    lines.append(f"  - 📄 Docs: {', '.join(item.suggested_docs)}")
            lines.append("")
        return "\n".join(lines)


class AuditEvent(BaseModel):
    ts: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    thread_id: str
    node: str
    status: Literal["ok", "error", "start", "end"] = "ok"
    latency_ms: float = 0.0
    input_digest: str = ""
    output_digest: str = ""
    sources: list[str] = Field(default_factory=list)
    model: str = ""
    detail: dict = Field(default_factory=dict)
