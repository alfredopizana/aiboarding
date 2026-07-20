"""Embedding providers (SPEC-002 §3, decision 3).

- `openai`: real embeddings via langchain-openai.
- `hashing`: deterministic, offline, dependency-free — good for tests/demo.
"""

from __future__ import annotations

import hashlib
import math
import re
from abc import ABC, abstractmethod
from collections import Counter

_TOKEN_RE = re.compile(r"[a-záéíóúñü0-9]+", re.IGNORECASE)
_DIM = 256

# High-frequency function words (en + es) carry no retrieval signal and, with a
# growing corpus, drown out content words in the bag-of-words vectors.
_STOPWORDS = frozenset(
    "a an and are as at be but by can do does for from how i in is it my of on or our so "
    "that the this to we what when where which who why will with you your "
    "el la los las un una unos unas de del en es son y o u que como cómo cuando donde dónde "
    "para por con sin mi mis se su sus lo al".split()
)


class Embedder(ABC):
    @abstractmethod
    def embed(self, texts: list[str]) -> list[list[float]]: ...


class HashingEmbedder(Embedder):
    """Bag-of-words hashed into a fixed-size vector. Deterministic and offline.

    Stopwords are dropped and term frequency is sublinear (1 + log tf), so
    content words dominate the vector instead of "how/do/the/de/la".
    """

    def embed(self, texts: list[str]) -> list[list[float]]:
        return [self._one(t) for t in texts]

    @staticmethod
    def _one(text: str) -> list[float]:
        tokens = _TOKEN_RE.findall(text.lower())
        kept = [t for t in tokens if t not in _STOPWORDS] or tokens
        vec = [0.0] * _DIM
        for token, tf in Counter(kept).items():
            idx = int(hashlib.md5(token.encode()).hexdigest(), 16) % _DIM
            vec[idx] += 1.0 + math.log(tf)
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
