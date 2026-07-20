"""Postgres + pgvector vector store — same interface as VectorStore.

Selected when a database URL is configured (see get_vectorstore). Keeps the app
stateless: chunks and embeddings live in Postgres, similarity runs in SQL.

Requires: pip install 'aiboarding[postgres]' and the `vector` extension
(created automatically if the DB role is allowed to CREATE EXTENSION).
"""

from __future__ import annotations

import logging

from aiboarding.knowledge.embeddings import Embedder
from aiboarding.models import Chunk, RetrievedChunk

logger = logging.getLogger(__name__)


def _psycopg_url(url: str) -> str:
    """psycopg3 wants a libpq URL (postgresql://…), not the SQLAlchemy +driver form."""
    if url.startswith("postgres://"):
        url = "postgresql://" + url[len("postgres://") :]
    return url.replace("postgresql+psycopg://", "postgresql://")


class PgVectorStore:
    def __init__(self, url: str, embedder: Embedder):
        import numpy as np  # noqa: F401  (ensures the extra is installed)
        import psycopg

        self.embedder = embedder
        self.url = _psycopg_url(url)
        # Bootstrap: create the `vector` extension with a plain connection first —
        # register_vector() below needs the type to already exist.
        with psycopg.connect(self.url) as conn:
            conn.execute("CREATE EXTENSION IF NOT EXISTS vector")
            conn.commit()
        # Determine embedding dimensionality from the active embedder.
        self._dim = len(embedder.embed(["dimension probe"])[0])
        with self._conn() as conn:
            conn.execute(
                f"""
                CREATE TABLE IF NOT EXISTS doc_chunks (
                    chunk_id  text PRIMARY KEY,
                    doc_id    text NOT NULL,
                    source    text,
                    title     text,
                    uri       text,
                    text      text,
                    position  int,
                    embedding vector({self._dim})
                )
                """
            )
            conn.execute("CREATE INDEX IF NOT EXISTS doc_chunks_doc_id ON doc_chunks (doc_id)")
            conn.commit()

    def _conn(self):
        import psycopg
        from pgvector.psycopg import register_vector

        conn = psycopg.connect(self.url)
        register_vector(conn)
        return conn

    # ── write ──────────────────────────────────────────────────────
    def upsert_document(self, doc_id: str, chunks: list[Chunk]) -> None:
        import numpy as np

        with self._conn() as conn:
            conn.execute("DELETE FROM doc_chunks WHERE doc_id = %s", (doc_id,))
            if chunks:
                vectors = self.embedder.embed([c.text for c in chunks])
                with conn.cursor() as cur:
                    for chunk, vec in zip(chunks, vectors, strict=True):
                        cur.execute(
                            """
                            INSERT INTO doc_chunks
                                (chunk_id, doc_id, source, title, uri, text, position, embedding)
                            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                            ON CONFLICT (chunk_id) DO UPDATE SET
                                doc_id=EXCLUDED.doc_id, source=EXCLUDED.source,
                                title=EXCLUDED.title, uri=EXCLUDED.uri, text=EXCLUDED.text,
                                position=EXCLUDED.position, embedding=EXCLUDED.embedding
                            """,
                            (
                                chunk.chunk_id, chunk.doc_id, chunk.source, chunk.title,
                                chunk.uri, chunk.text, chunk.position,
                                np.array(vec, dtype="float32"),
                            ),
                        )
            conn.commit()

    def persist(self) -> None:
        # No-op: Postgres commits on write. Kept for interface parity.
        return None

    # ── read ───────────────────────────────────────────────────────
    def retrieve(self, query: str, k: int = 5, min_score: float = 0.05) -> list[RetrievedChunk]:
        import numpy as np

        qvec = np.array(self.embedder.embed([query])[0], dtype="float32")
        with self._conn() as conn:
            rows = conn.execute(
                """
                SELECT chunk_id, doc_id, source, title, uri, text, position,
                       1 - (embedding <=> %s) AS score
                FROM doc_chunks
                ORDER BY embedding <=> %s
                LIMIT %s
                """,
                (qvec, qvec, k),
            ).fetchall()
        out: list[RetrievedChunk] = []
        for r in rows:
            score = float(r[7])
            if score < min_score:
                continue
            chunk = Chunk(
                chunk_id=r[0], doc_id=r[1], source=r[2], title=r[3],
                uri=r[4], text=r[5], position=r[6],
            )
            out.append(RetrievedChunk(chunk=chunk, score=round(score, 4)))
        return out

    def uri_titles(self) -> dict[str, str]:
        with self._conn() as conn:
            rows = conn.execute("SELECT DISTINCT uri, title FROM doc_chunks").fetchall()
        return {r[0]: r[1] for r in rows}

    def count_chunks(self) -> int:
        with self._conn() as conn:
            return int(conn.execute("SELECT count(*) FROM doc_chunks").fetchone()[0])

    def count_documents(self) -> int:
        with self._conn() as conn:
            return int(conn.execute("SELECT count(DISTINCT doc_id) FROM doc_chunks").fetchone()[0])
