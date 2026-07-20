"""LangSmith tracing setup.

When enabled, LangChain/LangGraph auto-export run traces to LangSmith. We only
need to populate the environment variables the LangChain runtime reads. This is
complementary to the local audit trail (AuditLogger), which keeps working.
"""

from __future__ import annotations

import logging
import os

from aiboarding.config import Settings

logger = logging.getLogger(__name__)

_configured = False


def configure_tracing(settings: Settings) -> bool:
    """Export LangSmith env vars if tracing is enabled. Idempotent. Returns active state."""
    global _configured
    if _configured or not settings.langsmith_tracing:
        return settings.langsmith_tracing
    if not settings.langsmith_api_key:
        logger.warning("LANGSMITH_TRACING is on but no API key set; skipping.")
        return False
    # Set both the modern (LANGSMITH_*) and legacy (LANGCHAIN_*) variable names.
    os.environ.setdefault("LANGSMITH_TRACING", "true")
    os.environ.setdefault("LANGCHAIN_TRACING_V2", "true")
    os.environ.setdefault("LANGSMITH_API_KEY", settings.langsmith_api_key)
    os.environ.setdefault("LANGCHAIN_API_KEY", settings.langsmith_api_key)
    os.environ.setdefault("LANGSMITH_PROJECT", settings.langsmith_project)
    os.environ.setdefault("LANGCHAIN_PROJECT", settings.langsmith_project)
    _configured = True
    logger.info("LangSmith tracing enabled (project=%s).", settings.langsmith_project)
    return True
