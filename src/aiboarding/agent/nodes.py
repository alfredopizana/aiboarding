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
    r"\b(doc|documentaci[oó]n|documentation|link|enlace|d[oó]nde encuentro|where (can i )?find|"
    r"wiki|runbook|manual)\b",
    re.I,
)
# Advice/reasoning questions must be answered with judgement, not a link dump —
# even when they mention "docs". Checked before _DOCS_RE.
_ADVICE_RE = re.compile(
    r"\b(recomiend|recommend|suggest|should i|do i|debo|deber[ií]a|qu[eé] (hago|hacer|me conviene)|"
    r"c[oó]mo (empiezo|deber[ií]a)|how (do|should) i|mejor|first|primero|prioriti|prioriza|vs\.?|"
    r"or (should|do)|o (agendo|leer|hacer))\b",
    re.I,
)

SYSTEM_PROMPT = (
    "You are AIboarding, a proactive onboarding assistant for a specific new hire. "
    "Give a direct, reasoned, PERSONALIZED answer — never just a list of links. "
    "Use the user's profile and their 90-day plan to tailor the advice: reference specific "
    "plan items, teammates, or docs and explain WHY they matter for this person right now. "
    "Prefer concrete next steps. Keep it concise (a short paragraph or a few bullets). "
    "Ground factual claims in the provided context; if the context is thin, still give sensible "
    "onboarding guidance and note what to verify. Answer in the same language as the question."
)


def classify_intent_heuristic(query: str) -> Intent | None:
    if _PLAN_RE.search(query):
        return "plan"
    if _CONNECT_RE.search(query):
        return "connect"
    if _ADVICE_RE.search(query):
        return "question"
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
        progress=None,
        repos: list[str] | None = None,
    ):
        self.store = store
        self.people = people
        self.llm = llm
        self.audit = audit
        self.plan_generator = plan_generator
        self.progress = progress  # ProgressStore | None — for plan-aware answers
        self.repos = repos or []

    # ── personalization context builders ───────────────────────────
    def _profile_context(self, user: UserProfile) -> str:
        line = (
            f"USER: {user.name} · role={user.role or 'unspecified'} · "
            f"team={user.team or 'unspecified'} · start_date={user.start_date or 'unspecified'}"
        )
        if self.repos:
            line += f"\nCODE REPOS: {', '.join(self.repos)}"
        return line

    def _plan_context(self, user: UserProfile) -> str:
        email = getattr(user, "email", "")
        if not (self.progress and email):
            return ""
        saved = self.progress.get_user(email)
        plan = self.progress.get_active_plan(saved.id) if saved else None
        if not plan:
            return ""
        lines = [f"USER'S 90-DAY PLAN: {plan.done_count}/{plan.total} items done. Pending next steps:"]
        for it in [i for i in plan.items if not i.done][:5]:
            lines.append(f"  - ({it.phase}) {it.title}: {it.description}")
        return "\n".join(lines)

    def _people_context(self, query: str, user: UserProfile):
        matches = self.people.match(query, team=user.team, limit=3)
        if not matches:
            return "", []
        lines = ["RELEVANT TEAMMATES:"]
        for m in matches:
            contact = m.person.slack or m.person.email or ""
            exp = ", ".join(m.person.expertise)
            lines.append(
                f"  - {m.person.name} ({m.person.role}, {m.person.team})"
                + (f" — {exp}" if exp else "")
                + (f" · {contact}" if contact else "")
            )
        return "\n".join(lines), matches

    def _personalized_answer(self, state: AgentState, retrieved: list) -> tuple[str, list]:
        """Build a profile/plan/people/docs context and let the LLM reason over it."""
        query = state["query"]
        user = state.get("user", UserProfile())
        people_ctx, matches = self._people_context(query, user)
        parts = [self._profile_context(user)]
        plan_ctx = self._plan_context(user)
        if plan_ctx:
            parts.append(plan_ctx)
        if people_ctx:
            parts.append(people_ctx)
        if retrieved:
            docs = "\n\n".join(f"[{r.chunk.title}]\n{r.chunk.text[:900]}" for r in retrieved)
            parts.append(f"CONTEXT:\n{docs}")
        user_msg = f"QUESTION: {query}\n\n" + "\n\n".join(parts)
        return self.llm.complete(SYSTEM_PROMPT, user_msg), matches

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
            answer, matches = self._personalized_answer(state, retrieved)
            rec["sources"] = [c.chunk_id for c in citations]
            rec["output_text"] = answer
            rec["detail"] = {"chunks": len(retrieved), "people": len(matches)}
        return {
            "retrieved": retrieved,
            "citations": citations,
            "answer": answer,
            "people_matches": matches,
        }

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
            if retrieved:
                # Reason first (personalized), then point to the specific docs.
                reasoning, matches = self._personalized_answer(state, retrieved)
                seen: set[str] = set()
                links = []
                for c in citations:
                    if c.uri in seen:
                        continue
                    seen.add(c.uri)
                    links.append(f"- **{c.title}** ({c.source}) — {c.uri}")
                answer = reasoning + "\n\n**Relevant documentation:**\n" + "\n".join(links)
            else:
                matches = []
                answer = "No documentation matched. Try `aiboarding ingest` to index more sources."
            rec["sources"] = [c.chunk_id for c in citations]
            rec["output_text"] = answer
        return {
            "retrieved": retrieved,
            "citations": citations,
            "answer": answer,
            "people_matches": matches,
        }

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
