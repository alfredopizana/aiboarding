"""Persistent vector store: JSON + cosine similarity (SPEC-002 decision 2).

Zero native dependencies; swap for Chroma/pgvector later behind the same API.
"""

from __future__ import annotations

import json
import math
from pathlib import Path

from aiboarding.knowledge.embeddings import Embedder
from aiboarding.models import Chunk, RetrievedChunk


def _cosine(a: list[float], b: list[float]) -> float:
    dot = sum(x * y for x, y in zip(a, b, strict=False))
    na = math.sqrt(sum(x * x for x in a)) or 1.0
    nb = math.sqrt(sum(y * y for y in b)) or 1.0
    return dot / (na * nb)


class VectorStore:
    def __init__(self, directory: str | Path, embedder: Embedder):
        self.directory = Path(directory)
        self.embedder = embedder
        self._file = self.directory / "store.json"
        self._chunks: dict[str, Chunk] = {}
        self._vectors: dict[str, list[float]] = {}
        self._load()

    # ── persistence ────────────────────────────────────────────────
    def _load(self) -> None:
        if not self._file.exists():
            return
        data = json.loads(self._file.read_text())
        self._chunks = {cid: Chunk(**c) for cid, c in data["chunks"].items()}
        self._vectors = data["vectors"]

    def persist(self) -> None:
        self.directory.mkdir(parents=True, exist_ok=True)
        payload = {
            "chunks": {cid: c.model_dump() for cid, c in self._chunks.items()},
            "vectors": self._vectors,
        }
        self._file.write_text(json.dumps(payload))

    # ── write ──────────────────────────────────────────────────────
    def upsert_document(self, doc_id: str, chunks: list[Chunk]) -> None:
        """Replace all chunks of doc_id with the new set (SPEC-003 §4)."""
        stale = [cid for cid in self._chunks if cid.startswith(f"{doc_id}:")]
        for cid in stale:
            self._chunks.pop(cid, None)
            self._vectors.pop(cid, None)
        if not chunks:
            return
        vectors = self.embedder.embed([c.text for c in chunks])
        for chunk, vec in zip(chunks, vectors, strict=True):
            self._chunks[chunk.chunk_id] = chunk
            self._vectors[chunk.chunk_id] = vec

    # ── read ───────────────────────────────────────────────────────
    def retrieve(self, query: str, k: int = 5, min_score: float = 0.05) -> list[RetrievedChunk]:
        if not self._chunks:
            return []
        qvec = self.embedder.embed([query])[0]
        scored = [
            (cid, _cosine(qvec, vec)) for cid, vec in self._vectors.items()
        ]
        scored.sort(key=lambda t: t[1], reverse=True)
        return [
            RetrievedChunk(chunk=self._chunks[cid], score=round(score, 4))
            for cid, score in scored[:k]
            if score >= min_score
        ]

    def uri_titles(self) -> dict[str, str]:
        """Map each known document URI to its title (for rendering doc links)."""
        return {c.uri: c.title for c in self._chunks.values()}

    def count_chunks(self) -> int:
        return len(self._chunks)

    def count_documents(self) -> int:
        return len({c.doc_id for c in self._chunks.values()})
