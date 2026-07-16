"""Paragraph-aware chunker (SPEC-003 §3)."""

from __future__ import annotations

from aiboarding.models import Chunk, SourceDocument

TARGET_SIZE = 1200
OVERLAP = 200


def chunk_document(doc: SourceDocument, target_size: int = TARGET_SIZE, overlap: int = OVERLAP) -> list[Chunk]:
    """Split by paragraphs targeting ~target_size chars with word-safe overlap."""
    paragraphs = [p.strip() for p in doc.content.split("\n\n") if p.strip()]
    pieces: list[str] = []
    current = ""
    for para in paragraphs:
        if current and len(current) + len(para) + 2 > target_size:
            pieces.append(current)
            # word-safe overlap tail
            tail = current[-overlap:]
            space = tail.find(" ")
            current = (tail[space + 1 :] + "\n\n" if space != -1 else "") + para
        else:
            current = f"{current}\n\n{para}" if current else para
        # hard-split oversize paragraphs
        while len(current) > target_size * 2:
            cut = current.rfind(" ", 0, target_size)
            cut = cut if cut > 0 else target_size
            pieces.append(current[:cut])
            current = current[cut:].lstrip()
    if current:
        pieces.append(current)

    return [
        Chunk(
            chunk_id=f"{doc.doc_id}:{i}",
            doc_id=doc.doc_id,
            source=doc.source,
            title=doc.title,
            uri=doc.uri,
            text=piece,
            position=i,
        )
        for i, piece in enumerate(pieces)
    ]
