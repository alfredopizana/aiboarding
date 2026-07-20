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
from aiboarding.knowledge.vectorstore import VectorStore, get_vectorstore
from aiboarding.persistence import ProgressStore, get_progress_store
from aiboarding.plans.generator import PlanGenerator
from aiboarding.tracing import configure_tracing


@dataclass
class Services:
    settings: Settings
    store: VectorStore
    people: PeopleDirectory
    llm: LLMClient
    audit: AuditLogger
    plan_generator: PlanGenerator
    agent: OnboardingAgent
    progress: ProgressStore


def build_services(settings: Settings | None = None) -> Services:
    settings = settings or get_settings()
    configure_tracing(settings)
    embedder = get_embedder(settings.embeddings_provider, settings.openai_api_key)
    store = get_vectorstore(settings, embedder)
    people = PeopleDirectory.from_yaml(settings.people_file)
    llm = get_llm(settings.llm_provider, settings.openai_api_key, settings.llm_model)
    audit = AuditLogger(settings.audit_dir)
    plan_generator = PlanGenerator(store, people, llm)
    progress = get_progress_store(
        settings.progress_backend, settings.db_path, settings.database_url
    )
    nodes = Nodes(
        store, people, llm, audit, plan_generator,
        progress=progress, repos=settings.github_repo_list,
    )
    agent = OnboardingAgent(nodes, audit)
    return Services(settings, store, people, llm, audit, plan_generator, agent, progress)
