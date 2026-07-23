"""Build the knowledge vector index and run sample queries."""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from knowledge.retrieval.semantic_search import build_knowledge_index, search_knowledge
from shared.schemas.knowledge import KnowledgeSearchRequest, SearchType


def main() -> None:
    count = build_knowledge_index()
    print(f"Indexed {count} chunks\n")

    samples = [
        ("What are your branch hours?", SearchType.HYBRID),
        ("Is OTP required for a 3000 birr wallet transfer?", SearchType.SEMANTIC),
        ("OTP wallet transfer threshold", SearchType.KEYWORD),
    ]
    for query, search_type in samples:
        response = search_knowledge(
            KnowledgeSearchRequest(
                query=query,
                searchType=search_type,
                maxResults=3,
                minRelevanceScore=0.1,
            )
        )
        print(f"Q [{search_type.value}]: {query}")
        for item in response.results:
            print(f"  - {item.relevance_score:.2f} | {item.title} | {item.source}")
        print()


if __name__ == "__main__":
    main()
