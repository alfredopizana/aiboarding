"""Connector contract (SPEC-003 §1)."""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Iterable

from aiboarding.models import SourceDocument


class Connector(ABC):
    name: str = "base"

    @abstractmethod
    def is_configured(self) -> bool:
        """Whether this connector has enough config to run."""

    @abstractmethod
    def fetch(self) -> Iterable[SourceDocument]:
        """Yield normalized documents from the source."""
