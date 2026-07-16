"""Append-only JSONL audit trail per thread (SPEC-004 §4)."""

from __future__ import annotations

import json
import time
from contextlib import contextmanager
from pathlib import Path

from aiboarding.models import AuditEvent, digest


class AuditLogger:
    def __init__(self, audit_dir: str | Path):
        self.audit_dir = Path(audit_dir)

    def _file(self, thread_id: str) -> Path:
        safe = "".join(c if c.isalnum() or c in "-_" else "_" for c in thread_id)
        return self.audit_dir / f"{safe}.jsonl"

    def log(self, event: AuditEvent) -> None:
        self.audit_dir.mkdir(parents=True, exist_ok=True)
        with self._file(event.thread_id).open("a") as fh:
            fh.write(event.model_dump_json() + "\n")

    def read(self, thread_id: str) -> list[AuditEvent]:
        path = self._file(thread_id)
        if not path.exists():
            return []
        return [AuditEvent(**json.loads(line)) for line in path.read_text().splitlines() if line]

    @contextmanager
    def node_span(self, thread_id: str, node: str, input_text: str = "", model: str = ""):
        """Context manager: times a node and logs ok/error with digests."""
        start = time.perf_counter()
        record: dict = {"sources": [], "detail": {}, "output_text": ""}
        try:
            yield record
            self.log(
                AuditEvent(
                    thread_id=thread_id,
                    node=node,
                    status="ok",
                    latency_ms=round((time.perf_counter() - start) * 1000, 2),
                    input_digest=digest(input_text) if input_text else "",
                    output_digest=digest(record["output_text"]) if record["output_text"] else "",
                    sources=record["sources"],
                    model=model,
                    detail=record["detail"],
                )
            )
        except Exception as exc:
            self.log(
                AuditEvent(
                    thread_id=thread_id,
                    node=node,
                    status="error",
                    latency_ms=round((time.perf_counter() - start) * 1000, 2),
                    input_digest=digest(input_text) if input_text else "",
                    model=model,
                    detail={"error": str(exc)[:500]},
                )
            )
            raise
