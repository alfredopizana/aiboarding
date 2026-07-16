"""LLM client abstraction (SPEC-004 §6)."""

from __future__ import annotations

from abc import ABC, abstractmethod


class LLMClient(ABC):
    model: str = "unknown"

    @abstractmethod
    def complete(self, system: str, user: str) -> str: ...


class FakeLLM(LLMClient):
    """Deterministic offline LLM: echoes structured template answers.

    Used for tests, demos, and CI without API keys (SPEC-002 decision 3).
    """

    model = "fake"

    def complete(self, system: str, user: str) -> str:
        # Extract the CONTEXT block if present and produce a grounded summary.
        if "CONTEXT:" in user:
            context = user.split("CONTEXT:", 1)[1].strip()
            first_lines = [ln.strip() for ln in context.splitlines() if ln.strip()][:6]
            body = "\n".join(f"> {ln}" for ln in first_lines)
            return (
                "Based on the ingested documentation, here is what I found:\n\n"
                f"{body}\n\n"
                "(offline deterministic answer — configure AIBOARDING_LLM_PROVIDER=openai for full synthesis)"
            )
        return "I could not find relevant context. Try ingesting more documents or ask a teammate."


class OpenAILLM(LLMClient):
    def __init__(self, api_key: str, model: str = "gpt-4o-mini"):
        from langchain_openai import ChatOpenAI

        self.model = model
        self._client = ChatOpenAI(model=model, api_key=api_key, temperature=0.2)

    def complete(self, system: str, user: str) -> str:
        resp = self._client.invoke([("system", system), ("user", user)])
        return str(resp.content)


def get_llm(provider: str, api_key: str = "", model: str = "gpt-4o-mini") -> LLMClient:
    if provider == "openai":
        return OpenAILLM(api_key, model)
    return FakeLLM()
