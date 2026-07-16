"""Shared fixtures: fully offline services (fake LLM + hashing embeddings)."""

from __future__ import annotations

from pathlib import Path

import pytest

from aiboarding.agent.audit import AuditLogger
from aiboarding.agent.graph import OnboardingAgent
from aiboarding.agent.llm import FakeLLM
from aiboarding.agent.nodes import Nodes
from aiboarding.connectors.local import LocalConnector
from aiboarding.ingestion.pipeline import run_ingestion
from aiboarding.knowledge.embeddings import HashingEmbedder
from aiboarding.knowledge.people import PeopleDirectory
from aiboarding.knowledge.vectorstore import VectorStore
from aiboarding.plans.generator import PlanGenerator

REPO_ROOT = Path(__file__).parent.parent
SAMPLE_DOCS = REPO_ROOT / "data" / "sample_docs"
PEOPLE_YAML = REPO_ROOT / "data" / "people.yaml"


@pytest.fixture
def store(tmp_path) -> VectorStore:
    return VectorStore(tmp_path / "vs", HashingEmbedder())


@pytest.fixture
def populated_store(store) -> VectorStore:
    run_ingestion([LocalConnector(SAMPLE_DOCS)], store)
    return store


@pytest.fixture
def people() -> PeopleDirectory:
    return PeopleDirectory.from_yaml(PEOPLE_YAML)


@pytest.fixture
def audit(tmp_path) -> AuditLogger:
    return AuditLogger(tmp_path / "audit")


@pytest.fixture
def agent(populated_store, people, audit) -> OnboardingAgent:
    llm = FakeLLM()
    plan_gen = PlanGenerator(populated_store, people, llm)
    nodes = Nodes(populated_store, people, llm, audit, plan_gen)
    return OnboardingAgent(nodes, audit)
