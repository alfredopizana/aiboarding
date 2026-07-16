"""LangGraph assembly + public run_agent entrypoint (SPEC-004 §2)."""

from __future__ import annotations

import uuid

from langgraph.graph import END, START, StateGraph

from aiboarding.agent.audit import AuditLogger
from aiboarding.agent.nodes import Nodes
from aiboarding.agent.state import AgentState
from aiboarding.models import AuditEvent, UserProfile, digest


def build_graph(nodes: Nodes):
    graph = StateGraph(AgentState)
    graph.add_node("classify_intent", nodes.classify_intent)
    graph.add_node("answer_question", nodes.answer_question)
    graph.add_node("suggest_people", nodes.suggest_people)
    graph.add_node("generate_plan", nodes.generate_plan)
    graph.add_node("refer_docs", nodes.refer_docs)
    graph.add_node("finalize", nodes.finalize)

    graph.add_edge(START, "classify_intent")
    graph.add_conditional_edges(
        "classify_intent",
        lambda state: state["intent"],
        {
            "question": "answer_question",
            "connect": "suggest_people",
            "plan": "generate_plan",
            "docs": "refer_docs",
        },
    )
    for node in ("answer_question", "suggest_people", "generate_plan", "refer_docs"):
        graph.add_edge(node, "finalize")
    graph.add_edge("finalize", END)
    return graph.compile()


class OnboardingAgent:
    def __init__(self, nodes: Nodes, audit: AuditLogger):
        self.nodes = nodes
        self.audit = audit
        self.graph = build_graph(nodes)

    def run(self, query: str, user: UserProfile | None = None, thread_id: str | None = None) -> AgentState:
        thread_id = thread_id or f"thr_{uuid.uuid4().hex[:12]}"
        user = user or UserProfile()
        self.audit.log(
            AuditEvent(
                thread_id=thread_id,
                node="graph_start",
                status="start",
                input_digest=digest(query),
                detail={"query_len": len(query), "user_role": user.role},
            )
        )
        state: AgentState = {
            "thread_id": thread_id,
            "user": user,
            "query": query,
            "citations": [],
            "retrieved": [],
            "people_matches": [],
        }
        result = self.graph.invoke(state)
        self.audit.log(
            AuditEvent(
                thread_id=thread_id,
                node="graph_end",
                status="end",
                output_digest=digest(result.get("answer", "")),
                detail={"intent": result.get("intent")},
            )
        )
        result["thread_id"] = thread_id
        return result
