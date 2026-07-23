"""Load and inspect markdown knowledge sources."""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from knowledge.ingestion.loader import load_markdown_sources


def main() -> None:
    documents = load_markdown_sources()
    print(f"Loaded {len(documents)} documents:")
    for doc in documents:
        print(f"- {doc.document_id} | {doc.title} | {doc.file_name} | tags={len(doc.tags)}")


if __name__ == "__main__":
    main()
