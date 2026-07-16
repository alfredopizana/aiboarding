"""Service container: wires settings → embedder/store/people/llm/agent."""

from __future__ import annotations

from dataclasses import dataclass

from aiboarding.agent.audit import AuditLogger
from aiboarding.agent.graph import OnboardingAgent
from aiboarding.agent.llm import LLMClient, get_llm
from aiboarding.agent.nodes import Nodes
from aiboarding.config import Settings, get_settings
from aiboarding.knowledge.embeddings import get_embedder
from aiboarding.knowledge.people import PeopleDirectory
from aiboarding.knowledge.vectorstore import VectorStore
from aiboarding.plans.generator import PlanGenerator


@dataclass
class Services:
    settings: Settings
    store: VectorStore
    people: PeopleDirectory
    llm: LLMClient
    audit: AuditLogger
    plan_generator: PlanGenerator
    agent: OnboardingAgent


def build_services(settings: Settings | None = None) -> Services:
    settings = settings or get_settings()
    embedder = get_embedder(settings.embeddings_provider, settings.openai_api_key)
    store = VectorStore(settings.vectorstore_dir, embedder)
    people = PeopleDirectory.from_yaml(settings.people_file)
    llm = get_llm(settings.llm_provider, settings.openai_api_key, settings.llm_model)
    audit = AuditLogger(settings.audit_dir)
    plan_generator = PlanGenerator(store, people, llm)
    nodes = Nodes(store, people, llm, audit, plan_generator)
    agent = OnboardingAgent(nodes, audit)
    return Services(settings, store, people, llm, audit, plan_generator, agent)
