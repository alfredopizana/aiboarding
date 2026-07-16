"""Graph nodes (SPEC-004 §2–§5). Each node is pure-ish and audited via AuditLogger."""

from __future__ import annotations

import re

from aiboarding.agent.audit import AuditLogger
from aiboarding.agent.llm import LLMClient
from aiboarding.agent.state import AgentState, Intent
from aiboarding.knowledge.people import PeopleDirectory
from aiboarding.knowledge.vectorstore import VectorStore
from aiboarding.models import Citation, UserProfile

# ── intent heuristics (SPEC-004 §3) ─────────────────────────────────
_PLAN_RE = re.compile(r"\b(90|noventa|success plan|plan de \w+|onboarding plan|30.60.90)\b", re.I)
_CONNECT_RE = re.compile(
    r"\b(qui[eé]n|who|contact|connect|hablar con|talk to|expert|buddy|mentor|reach out)\b", re.I
)
_DOCS_RE = re.compile(
    r"\b(doc|documentaci[oó]n|documentation|link|enlace|d[oó]nde encuentro|where (can i )?find|wiki|runbook|manual)\b",
    re.I,
)

SYSTEM_PROMPT = (
    "You are AIboarding, an onboarding assistant. Answer using ONLY the provided context. "
    "Cite sources by title. If the context is insufficient, say so and suggest asking a teammate. "
    "Answer in the same language as the question."
)


def classify_intent_heuristic(query: str) -> Intent | None:
    if _PLAN_RE.search(query):
        return "plan"
    if _CONNECT_RE.search(query):
        return "connect"
    if _DOCS_RE.search(query):
        return "docs"
    return None


class Nodes:
    """Node implementations bound to concrete services."""

    def __init__(
        self,
        store: VectorStore,
        people: PeopleDirectory,
        llm: LLMClient,
        audit: AuditLogger,
        plan_generator=None,
    ):
        self.store = store
        self.people = people
        self.llm = llm
        self.audit = audit
        self.plan_generator = plan_generator

    # ── classify ───────────────────────────────────────────────────
    def classify_intent(self, state: AgentState) -> AgentState:
        query = state["query"]
        with self.audit.node_span(state["thread_id"], "classify_intent", query) as rec:
            intent = classify_intent_heuristic(query)
            method = "heuristic"
            if intent is None and self.llm.model != "fake":
                raw = self.llm.complete(
                    "Classify the user query into exactly one word: question, connect, plan, or docs.",
                    query,
                ).strip().lower()
                intent = raw if raw in ("question", "connect", "plan", "docs") else "question"  # type: ignore[assignment]
                method = "llm"
            if intent is None:
                intent = "question"
            rec["output_text"] = intent
            rec["detail"] = {"intent": intent, "method": method}
        return {"intent": intent}

    # ── question answering with citations ─────────────────────────
    def answer_question(self, state: AgentState) -> AgentState:
        query = state["query"]
        with self.audit.node_span(
            state["thread_id"], "answer_question", query, model=self.llm.model
        ) as rec:
            retrieved = self.store.retrieve(query, k=5)
            citations = [
                Citation(
                    title=r.chunk.title,
                    uri=r.chunk.uri,
                    source=r.chunk.source,
                    chunk_id=r.chunk.chunk_id,
                    score=r.score,
                )
                for r in retrieved
            ]
            if retrieved:
                context = "\n\n".join(
                    f"[{r.chunk.title}]\n{r.chunk.text}" for r in retrieved
                )
                answer = self.llm.complete(SYSTEM_PROMPT, f"QUESTION: {query}\n\nCONTEXT:\n{context}")
            else:
                fallbacks = self.people.match(query, team=state.get("user", UserProfile()).team)
                names = ", ".join(m.person.name for m in fallbacks) or "your onboarding buddy"
                answer = (
                    "I couldn't find relevant documentation for that yet. "
                    f"Consider asking: {names}. You can also ingest more sources with `aiboarding ingest`."
                )
            rec["sources"] = [c.chunk_id for c in citations]
            rec["output_text"] = answer
            rec["detail"] = {"chunks": len(retrieved)}
        return {"retrieved": retrieved, "citations": citations, "answer": answer}

    # ── people matching ────────────────────────────────────────────
    def suggest_people(self, state: AgentState) -> AgentState:
        query = state["query"]
        user = state.get("user", UserProfile())
        with self.audit.node_span(state["thread_id"], "suggest_people", query) as rec:
            matches = self.people.match(query, team=user.team, limit=5)
            if matches:
                lines = ["Here's who you should connect with:", ""]
                for m in matches:
                    contact = m.person.slack or m.person.email or ""
                    lines.append(
                        f"- **{m.person.name}** — {m.person.role}, {m.person.team} ({m.reason})"
                        + (f" · {contact}" if contact else "")
                    )
                answer = "\n".join(lines)
            else:
                answer = (
                    "No specific expert matched that topic in the people directory. "
                    "Check with your manager or onboarding buddy."
                )
            rec["output_text"] = answer
            rec["detail"] = {"matches": [m.person.id for m in matches]}
        return {"people_matches": matches, "answer": answer, "citations": []}

    # ── plan generation ────────────────────────────────────────────
    def generate_plan(self, state: AgentState) -> AgentState:
        user = state.get("user", UserProfile())
        with self.audit.node_span(state["thread_id"], "generate_plan", user.model_dump_json()) as rec:
            plan = self.plan_generator.generate(user)
            answer = plan.to_markdown()
            rec["output_text"] = answer
            rec["detail"] = {"role": user.role, "phases": len(plan.phases)}
        return {"plan": plan, "answer": answer, "citations": []}

    # ── doc referral ───────────────────────────────────────────────
    def refer_docs(self, state: AgentState) -> AgentState:
        query = state["query"]
        with self.audit.node_span(state["thread_id"], "refer_docs", query) as rec:
            retrieved = self.store.retrieve(query, k=5)
            citations = [
                Citation(
                    title=r.chunk.title,
                    uri=r.chunk.uri,
                    source=r.chunk.source,
                    chunk_id=r.chunk.chunk_id,
                    score=r.score,
                )
                for r in retrieved
            ]
            seen: set[str] = set()
            lines = ["Relevant documentation:", ""]
            for c in citations:
                if c.uri in seen:
                    continue
                seen.add(c.uri)
                lines.append(f"- **{c.title}** ({c.source}) — {c.uri}")
            answer = (
                "\n".join(lines)
                if len(lines) > 2
                else "No documentation matched. Try `aiboarding ingest` to index more sources."
            )
            rec["sources"] = [c.chunk_id for c in citations]
            rec["output_text"] = answer
        return {"retrieved": retrieved, "citations": citations, "answer": answer}

    # ── finalize ───────────────────────────────────────────────────
    def finalize(self, state: AgentState) -> AgentState:
        with self.audit.node_span(state["thread_id"], "finalize", state.get("answer", "")) as rec:
            answer = state.get("answer", "").strip() or "No answer produced."
            rec["output_text"] = answer
            rec["detail"] = {
                "intent": state.get("intent"),
                "citations": len(state.get("citations", [])),
            }
        return {"answer": answer}
