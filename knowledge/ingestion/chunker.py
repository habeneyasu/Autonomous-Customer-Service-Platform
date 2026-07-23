import re
from dataclasses import dataclass
from datetime import datetime

from knowledge.ingestion.loader import LoadedDocument

_HEADER = re.compile(r"^(#{1,3})\s+(.+)$")
_SLUG = re.compile(r"[^a-z0-9]+")

DEFAULT_OVERLAP_CHARS = 200


@dataclass(frozen=True)
class KnowledgeChunk:
    chunk_id: str
    document_id: str
    document_title: str
    parent_header: str
    section_header: str
    header_level: int
    content: str
    overlap_text: str
    contextual_text: str
    source: str
    source_file: str
    topic: str
    tags: tuple[str, ...]
    last_updated: datetime


@dataclass
class _Section:
    document_title: str
    parent_header: str
    section_header: str
    header_level: int
    lines: list[str]


def _slug(value: str) -> str:
    slug = _SLUG.sub("-", value.lower()).strip("-")
    return slug or "section"


def _overlap_tail(text: str, max_chars: int) -> str:
    """Take trailing content from the previous chunk for boundary context."""
    text = text.strip()
    if not text or max_chars <= 0:
        return ""

    if len(text) <= max_chars:
        return text

    tail = text[-max_chars:]
    for separator in ("\n", ". ", "? ", "! "):
        idx = tail.find(separator)
        if idx != -1:
            return tail[idx + len(separator) :].strip()
    return tail.strip()


def _build_contextual_text(
    document: LoadedDocument,
    section: _Section,
    *,
    overlap_text: str = "",
) -> str:
    path = section.document_title
    if section.parent_header and section.parent_header != section.document_title:
        path = f"{section.parent_header} > {section.section_header}"
    elif section.section_header != section.document_title:
        path = f"{section.document_title} > {section.section_header}"

    tags = ", ".join(document.tags) if document.tags else "none"
    body = "\n".join(section.lines).strip()

    parts = [
        f"Document: {document.title}",
        f"Section: {path}",
        f"Topic: {document.topic}",
        f"Tags: {tags}",
        f"Source: {document.source}",
    ]
    if overlap_text:
        parts.extend(["", "Overlap from previous section:", overlap_text])
    parts.extend(["", body])
    return "\n".join(parts)


def _flush(
    document: LoadedDocument,
    section: _Section | None,
    chunks: list[_Section],
) -> None:
    if section is None:
        return
    body = "\n".join(section.lines).strip()
    if body:
        chunks.append(section)


def _finalize_chunks(
    document: LoadedDocument,
    sections: list[_Section],
    *,
    overlap_chars: int,
) -> list[KnowledgeChunk]:
    chunks: list[KnowledgeChunk] = []
    previous_body = ""

    for index, section in enumerate(sections, start=1):
        body = "\n".join(section.lines).strip()
        overlap_text = _overlap_tail(previous_body, overlap_chars)
        chunk_id = f"{document.document_id}::{_slug(section.section_header)}-{index:02d}"

        chunks.append(
            KnowledgeChunk(
                chunk_id=chunk_id,
                document_id=document.document_id,
                document_title=section.document_title,
                parent_header=section.parent_header,
                section_header=section.section_header,
                header_level=section.header_level,
                content=body,
                overlap_text=overlap_text,
                contextual_text=_build_contextual_text(
                    document,
                    section,
                    overlap_text=overlap_text,
                ),
                source=document.source,
                source_file=document.file_name,
                topic=document.topic,
                tags=document.tags,
                last_updated=document.last_updated,
            )
        )
        previous_body = body

    return chunks


def chunk_document(
    document: LoadedDocument,
    *,
    overlap_chars: int = DEFAULT_OVERLAP_CHARS,
) -> list[KnowledgeChunk]:
    """Split markdown by headers and add trailing overlap between adjacent sections."""
    sections: list[_Section] = []
    current: _Section | None = None

    h1 = document.title
    h2 = ""

    for line in document.content.splitlines():
        match = _HEADER.match(line)
        if not match:
            if current is not None:
                current.lines.append(line)
            continue

        _flush(document, current, sections)
        level = len(match.group(1))
        title = match.group(2).strip()

        if level == 1:
            h1 = title
            h2 = ""
            current = None
            continue

        if level == 2:
            h2 = title
            current = _Section(
                document_title=h1,
                parent_header=h1,
                section_header=h2,
                header_level=2,
                lines=[],
            )
            continue

        current = _Section(
            document_title=h1,
            parent_header=h2 or h1,
            section_header=title,
            header_level=3,
            lines=[],
        )

    _flush(document, current, sections)
    return _finalize_chunks(document, sections, overlap_chars=overlap_chars)


def chunk_documents(
    documents: list[LoadedDocument],
    *,
    overlap_chars: int = DEFAULT_OVERLAP_CHARS,
) -> list[KnowledgeChunk]:
    all_chunks: list[KnowledgeChunk] = []
    for document in documents:
        all_chunks.extend(chunk_document(document, overlap_chars=overlap_chars))
    return all_chunks
