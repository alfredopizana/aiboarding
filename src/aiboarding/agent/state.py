"""Agent state (SPEC-004 §1)."""

from __future__ import annotations

from typing import Literal, TypedDict

from aiboarding.models import Citation, PersonMatch, RetrievedChunk, SuccessPlan, UserProfile

Intent = Literal["question", "connect", "plan", "docs"]


class AgentState(TypedDict, total=False):
    thread_id: str
    user: UserProfile
    query: str
    intent: Intent | None
    retrieved: list[RetrievedChunk]
    people_matches: list[PersonMatch]
    plan: SuccessPlan | None
    answer: str
    citations: list[Citation]
