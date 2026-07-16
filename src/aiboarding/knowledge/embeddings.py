"""Embedding providers (SPEC-002 §3, decision 3).

- `openai`: real embeddings via langchain-openai.
- `hashing`: deterministic, offline, dependency-free — good for tests/demo.
"""

from __future__ import annotations

import hashlib
import math
import re
from abc import ABC, abstractmethod

_TOKEN_RE = re.compile(r"[a-záéíóúñü0-9]+", re.IGNORECASE)
_DIM = 256


class Embedder(ABC):
    @abstractmethod
    def embed(self, texts: list[str]) -> list[list[float]]: ...


class HashingEmbedder(Embedder):
    """Bag-of-words hashed into a fixed-size vector. Deterministic and offline."""

    def embed(self, texts: list[str]) -> list[list[float]]:
        return [self._one(t) for t in texts]

    @staticmethod
    def _one(text: str) -> list[float]:
        vec = [0.0] * _DIM
        for token in _TOKEN_RE.findall(text.lower()):
            idx = int(hashlib.md5(token.encode()).hexdigest(), 16) % _DIM
            vec[idx] += 1.0
        norm = math.sqrt(sum(v * v for v in vec)) or 1.0
        return [v / norm for v in vec]


class OpenAIEmbedder(Embedder):
    def __init__(self, api_key: str, model: str = "text-embedding-3-small"):
        from langchain_openai import OpenAIEmbeddings

        self._client = OpenAIEmbeddings(model=model, api_key=api_key)

    def embed(self, texts: list[str]) -> list[list[float]]:
        return self._client.embed_documents(texts)


def get_embedder(provider: str, api_key: str = "") -> Embedder:
    if provider == "openai":
        return OpenAIEmbedder(api_key)
    return HashingEmbedder()
