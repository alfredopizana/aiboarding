"""Progress store: abstract interface + SQLite implementation.

`ProgressStore` is the swappable surface. Today it is backed by SQLite via
SQLModel; a `FirebaseProgressStore` can implement the same methods later and be
selected through `settings.progress_backend` without changing any caller.
"""

from __future__ import annotations

import json
import re
import uuid
from abc import ABC, abstractmethod
from datetime import datetime, timezone
from pathlib import Path

from pydantic import BaseModel
from sqlalchemy import event
from sqlmodel import Session, SQLModel, create_engine, select

from aiboarding.models import SuccessPlan, UserProfile
from aiboarding.persistence.tables import (
    ChatMessageRecord,
    PlanItemRecord,
    PlanRecord,
    UserRecord,
)


# ── Return models (backend-agnostic) ────────────────────────────────────────
class StoredUser(BaseModel):
    id: str
    email: str
    name: str
    role: str
    team: str
    start_date: str | None = None


class StoredItem(BaseModel):
    id: int
    phase: str
    objective: str
    category: str
    title: str
    description: str
    suggested_contacts: list[str]
    suggested_docs: list[str]
    done: bool


class StoredMessage(BaseModel):
    id: int
    role: str
    content: str
    thread_id: str = ""
    created_at: datetime


class StoredPlan(BaseModel):
    id: str
    user_id: str
    generated_at: datetime
    summary: str
    items: list[StoredItem]

    @property
    def total(self) -> int:
        return len(self.items)

    @property
    def done_count(self) -> int:
        return sum(1 for i in self.items if i.done)

    @property
    def progress(self) -> float:
        return self.done_count / self.total if self.total else 0.0


def _slug(email: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", email.lower()).strip("-") or uuid.uuid4().hex[:8]


# ── Abstract interface ──────────────────────────────────────────────────────
class ProgressStore(ABC):
    @abstractmethod
    def upsert_user(self, profile: UserProfile, email: str) -> StoredUser: ...

    @abstractmethod
    def get_user(self, email: str) -> StoredUser | None: ...

    @abstractmethod
    def save_plan(self, user_id: str, plan: SuccessPlan) -> StoredPlan: ...

    @abstractmethod
    def get_active_plan(self, user_id: str) -> StoredPlan | None: ...

    @abstractmethod
    def set_item_done(self, item_id: int, done: bool) -> None: ...

    @abstractmethod
    def save_message(self, user_id: str, role: str, content: str, thread_id: str = "") -> None: ...

    @abstractmethod
    def get_history(self, user_id: str, limit: int = 100) -> list[StoredMessage]: ...

    @abstractmethod
    def clear_history(self, user_id: str) -> int: ...


# ── SQLite implementation ───────────────────────────────────────────────────
class SQLiteProgressStore(ProgressStore):
    def __init__(self, db_path: str | Path):
        # Resolve to an absolute path so the DB location is independent of the
        # process CWD (Streamlit launches in a subprocess whose cwd may differ).
        db_path = Path(db_path).expanduser().resolve()
        db_path.parent.mkdir(parents=True, exist_ok=True)
        self.engine = create_engine(
            f"sqlite:///{db_path}",
            connect_args={"check_same_thread": False, "timeout": 30},
        )

        # WAL mode + a busy timeout make concurrent access (Streamlit reruns,
        # multiple sessions) robust and avoid spurious readonly/locked errors.
        @event.listens_for(self.engine, "connect")
        def _pragmas(dbapi_conn, _record):  # pragma: no cover - trivial
            cur = dbapi_conn.cursor()
            cur.execute("PRAGMA journal_mode=WAL")
            cur.execute("PRAGMA busy_timeout=5000")
            cur.close()

        SQLModel.metadata.create_all(self.engine)

    def upsert_user(self, profile: UserProfile, email: str) -> StoredUser:
        uid = _slug(email)
        with Session(self.engine) as s:
            rec = s.get(UserRecord, uid)
            if rec is None:
                rec = UserRecord(id=uid, email=email)
            rec.name = profile.name
            rec.role = profile.role
            rec.team = profile.team
            rec.start_date = profile.start_date
            s.add(rec)
            s.commit()
            s.refresh(rec)
            return _to_user(rec)

    def get_user(self, email: str) -> StoredUser | None:
        with Session(self.engine) as s:
            rec = s.get(UserRecord, _slug(email))
            return _to_user(rec) if rec else None

    def save_plan(self, user_id: str, plan: SuccessPlan) -> StoredPlan:
        plan_id = uuid.uuid4().hex[:16]
        with Session(self.engine) as s:
            # Deactivate any previous active plans for this user.
            for old in s.exec(
                select(PlanRecord).where(PlanRecord.user_id == user_id, PlanRecord.active)
            ).all():
                old.active = False
                s.add(old)
            s.add(PlanRecord(id=plan_id, user_id=user_id, summary=plan.summary, active=True))
            pos = 0
            for phase in plan.phases:
                for item in phase.items:
                    s.add(
                        PlanItemRecord(
                            plan_id=plan_id,
                            phase=phase.name,
                            objective=phase.objective,
                            category=item.category,
                            title=item.title,
                            description=item.description,
                            suggested_contacts=json.dumps(item.suggested_contacts),
                            suggested_docs=json.dumps(item.suggested_docs),
                            position=pos,
                            done=item.done,
                        )
                    )
                    pos += 1
            s.commit()
        got = self.get_active_plan(user_id)
        assert got is not None
        return got

    def get_active_plan(self, user_id: str) -> StoredPlan | None:
        with Session(self.engine) as s:
            plan = s.exec(
                select(PlanRecord).where(PlanRecord.user_id == user_id, PlanRecord.active)
            ).first()
            if plan is None:
                return None
            items = s.exec(
                select(PlanItemRecord)
                .where(PlanItemRecord.plan_id == plan.id)
                .order_by(PlanItemRecord.position)
            ).all()
            return StoredPlan(
                id=plan.id,
                user_id=plan.user_id,
                generated_at=plan.generated_at,
                summary=plan.summary,
                items=[_to_item(i) for i in items],
            )

    def set_item_done(self, item_id: int, done: bool) -> None:
        with Session(self.engine) as s:
            item = s.get(PlanItemRecord, item_id)
            if item is None:
                return
            item.done = done
            item.done_at = datetime.now(timezone.utc) if done else None
            s.add(item)
            s.commit()

    def save_message(self, user_id: str, role: str, content: str, thread_id: str = "") -> None:
        with Session(self.engine) as s:
            s.add(
                ChatMessageRecord(
                    user_id=user_id, role=role, content=content, thread_id=thread_id
                )
            )
            s.commit()

    def get_history(self, user_id: str, limit: int = 100) -> list[StoredMessage]:
        with Session(self.engine) as s:
            rows = s.exec(
                select(ChatMessageRecord)
                .where(ChatMessageRecord.user_id == user_id)
                .order_by(ChatMessageRecord.id)
                .limit(limit)
            ).all()
            return [
                StoredMessage(
                    id=r.id or 0,
                    role=r.role,
                    content=r.content,
                    thread_id=r.thread_id,
                    created_at=r.created_at,
                )
                for r in rows
            ]

    def clear_history(self, user_id: str) -> int:
        """Delete a user's persisted conversation history. Returns rows removed."""
        with Session(self.engine) as s:
            rows = s.exec(
                select(ChatMessageRecord).where(ChatMessageRecord.user_id == user_id)
            ).all()
            for r in rows:
                s.delete(r)
            s.commit()
            return len(rows)


def _to_user(rec: UserRecord) -> StoredUser:
    return StoredUser(
        id=rec.id, email=rec.email, name=rec.name, role=rec.role,
        team=rec.team, start_date=rec.start_date,
    )


def _to_item(rec: PlanItemRecord) -> StoredItem:
    return StoredItem(
        id=rec.id or 0,
        phase=rec.phase,
        objective=rec.objective,
        category=rec.category,
        title=rec.title,
        description=rec.description,
        suggested_contacts=json.loads(rec.suggested_contacts or "[]"),
        suggested_docs=json.loads(rec.suggested_docs or "[]"),
        done=rec.done,
    )


def get_progress_store(backend: str, db_path: str | Path) -> ProgressStore:
    if backend == "sqlite":
        return SQLiteProgressStore(db_path)
    # Future: if backend == "firebase": return FirebaseProgressStore(...)
    raise ValueError(f"Unknown progress backend: {backend!r}")
