"""FastAPI REST API (SPEC-006 §1)."""

from __future__ import annotations

import logging

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from aiboarding import __version__
from aiboarding.connectors import build_connectors
from aiboarding.container import Services, build_services
from aiboarding.ingestion.pipeline import run_ingestion
from aiboarding.models import AuditEvent, Citation, PersonMatch, SuccessPlan, UserProfile

logger = logging.getLogger(__name__)


class AskRequest(BaseModel):
    query: str
    user: UserProfile | None = None


class AskResponse(BaseModel):
    thread_id: str
    intent: str | None
    answer: str
    citations: list[Citation]
    people: list[PersonMatch]


class PlanResponse(BaseModel):
    thread_id: str
    plan: SuccessPlan
    markdown: str


class IngestRequest(BaseModel):
    source: str = "all"  # local|confluence|gdrive|github|all
    path: str | None = None


def create_app(services: Services | None = None) -> FastAPI:
    app = FastAPI(title="AIboarding", version=__version__)
    svc = services or build_services()

    @app.get("/health")
    def health():
        return {
            "status": "ok",
            "version": __version__,
            "docs_indexed": svc.store.count_documents(),
            "chunks": svc.store.count_chunks(),
            "people": len(svc.people.people),
            "llm_provider": svc.settings.llm_provider,
        }

    @app.post("/ask", response_model=AskResponse)
    def ask(req: AskRequest):
        try:
            result = svc.agent.run(req.query, user=req.user)
        except Exception as exc:  # noqa: BLE001
            logger.exception("agent failure")
            raise HTTPException(status_code=502, detail=f"Agent error: {exc}") from exc
        return AskResponse(
            thread_id=result["thread_id"],
            intent=result.get("intent"),
            answer=result.get("answer", ""),
            citations=result.get("citations", []),
            people=result.get("people_matches", []),
        )

    @app.post("/plan", response_model=PlanResponse)
    def plan(user: UserProfile):
        result = svc.agent.run(
            f"Generate my 90 day success plan for role {user.role}", user=user
        )
        plan_obj = result.get("plan")
        if plan_obj is None:  # force plan intent regardless of routing
            plan_obj = svc.plan_generator.generate(user)
        return PlanResponse(
            thread_id=result["thread_id"], plan=plan_obj, markdown=plan_obj.to_markdown()
        )

    @app.get("/people", response_model=list[PersonMatch])
    def people(topic: str, team: str = ""):
        return svc.people.match(topic, team=team, limit=5)

    @app.post("/ingest")
    def ingest(req: IngestRequest):
        connectors = build_connectors(svc.settings, local_path=req.path)
        selected = (
            list(connectors.values()) if req.source == "all" else [connectors.get(req.source)]
        )
        if not selected or selected[0] is None:
            raise HTTPException(status_code=422, detail=f"Unknown source: {req.source}")
        results = run_ingestion([c for c in selected if c], svc.store)
        return {
            "results": [r.__dict__ for r in results],
            "total_docs": sum(r.documents for r in results),
            "total_chunks": sum(r.chunks for r in results),
        }

    @app.get("/audit/{thread_id}", response_model=list[AuditEvent])
    def audit(thread_id: str):
        events = svc.audit.read(thread_id)
        if not events:
            raise HTTPException(status_code=404, detail="thread not found")
        return events

    return app


app = None  # lazy: use `aiboarding serve` or create_app()
