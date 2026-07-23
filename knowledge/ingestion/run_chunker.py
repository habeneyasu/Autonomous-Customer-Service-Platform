"""Inspect header-based contextual chunks."""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from knowledge.ingestion.chunker import chunk_documents
from knowledge.ingestion.loader import load_markdown_sources


def main() -> None:
    documents = load_markdown_sources()
    chunks = chunk_documents(documents)
    print(f"Loaded {len(documents)} documents -> {len(chunks)} chunks\n")

    for chunk in chunks:
        overlap_note = f"{len(chunk.overlap_text)} overlap chars" if chunk.overlap_text else "no overlap"
        print(f"[{chunk.chunk_id}]")
        print(f"  section: {chunk.parent_header} > {chunk.section_header} (h{chunk.header_level})")
        print(f"  content: {len(chunk.content)} chars | {overlap_note} | contextual: {len(chunk.contextual_text)} chars")
        if chunk.overlap_text:
            preview = chunk.overlap_text.replace("\n", " ")[:80]
            print(f"  overlap: {preview}...")
        print()


if __name__ == "__main__":
    main()
