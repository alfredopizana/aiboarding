"""SQLModel tables for the SQLite persistence backend."""

from __future__ import annotations

from datetime import datetime, timezone

from sqlmodel import Field, SQLModel


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class UserRecord(SQLModel, table=True):
    __tablename__ = "users"

    id: str = Field(primary_key=True)  # slug derived from email
    email: str = Field(index=True, unique=True)
    name: str = ""
    role: str = ""
    team: str = ""
    start_date: str | None = None
    created_at: datetime = Field(default_factory=_utcnow)


class PlanRecord(SQLModel, table=True):
    __tablename__ = "plans"

    id: str = Field(primary_key=True)  # uuid hex
    user_id: str = Field(index=True)
    generated_at: datetime = Field(default_factory=_utcnow)
    summary: str = ""
    active: bool = Field(default=True, index=True)


class PlanItemRecord(SQLModel, table=True):
    __tablename__ = "plan_items"

    id: int | None = Field(default=None, primary_key=True)
    plan_id: str = Field(index=True)
    phase: str = ""
    objective: str = ""
    category: str = ""
    title: str = ""
    description: str = ""
    suggested_contacts: str = ""  # JSON-encoded list[str]
    suggested_docs: str = ""  # JSON-encoded list[str]
    position: int = 0
    done: bool = False
    done_at: datetime | None = None
