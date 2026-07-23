"""Token-based keyword search over knowledge chunks."""

from __future__ import annotations

import math
import re
from collections import Counter

from knowledge.ingestion.chunker import KnowledgeChunk
from shared.schemas.knowledge import KnowledgeDocument

_TOKEN = re.compile(r"[a-z0-9]+")

# Short function words that rarely help ranking for policy queries.
_STOPWORDS = frozenset(
    {
        "a",
        "an",
        "and",
        "are",
        "as",
        "at",
        "be",
        "by",
        "for",
        "from",
        "how",
        "in",
        "is",
        "it",
        "of",
        "on",
        "or",
        "the",
        "to",
        "what",
        "when",
        "where",
        "which",
        "who",
        "with",
        "your",
    }
)


def tokenize(text: str, *, drop_stopwords: bool = False) -> list[str]:
    tokens = _TOKEN.findall(text.lower())
    if drop_stopwords:
        return [token for token in tokens if token not in _STOPWORDS]
    return tokens


def keyword_search(
    query: str,
    chunks: list[KnowledgeChunk],
    *,
    top_k: int | None = None,
) -> list[KnowledgeDocument]:
    """Rank chunks by keyword overlap with title/tag boosts.

    Score is normalized to [0, 1]:
    - base: fraction of query tokens found in the chunk
    - header/tag hits get extra weight
    - consecutive phrase matches get a small bonus
    """
    query_tokens = tokenize(query, drop_stopwords=True)
    if not query_tokens:
        query_tokens = tokenize(query)
    if not query_tokens:
        return []

    query_counts = Counter(query_tokens)
    unique_query = list(dict.fromkeys(query_tokens))
    scored: list[KnowledgeDocument] = []

    for chunk in chunks:
        header_tokens = tokenize(chunk.section_header)
        tag_tokens = tokenize(" ".join(chunk.tags))
        body_tokens = tokenize(chunk.content)
        all_tokens = header_tokens + tag_tokens + body_tokens
        if not all_tokens:
            continue

        body_counts = Counter(body_tokens)
        header_set = set(header_tokens)
        tag_set = set(tag_tokens)
        all_set = set(all_tokens)

        matched = 0.0
        weight_sum = 0.0
        for token, q_count in query_counts.items():
            weight = 1.0
            if token in header_set:
                weight = 2.0
            elif token in tag_set:
                weight = 1.5

            weight_sum += weight * q_count
            if token not in all_set:
                continue

            # Soft TF: diminishing returns for repeated body hits.
            tf = body_counts.get(token, 0) + (2 if token in header_set else 0) + (
                1 if token in tag_set else 0
            )
            matched += weight * min(q_count, 1 + math.log1p(tf))

        if matched <= 0 or weight_sum <= 0:
            continue

        coverage = len(set(unique_query) & all_set) / len(unique_query)
        tf_score = min(1.0, matched / weight_sum)
        phrase_bonus = _phrase_bonus(unique_query, all_tokens)
        score = min(1.0, 0.55 * coverage + 0.35 * tf_score + 0.10 * phrase_bonus)

        scored.append(
            KnowledgeDocument(
                document_id=chunk.chunk_id,
                title=chunk.section_header,
                excerpt=chunk.content[:240],
                relevance_score=round(score, 4),
                source=chunk.source,
            )
        )

    scored.sort(key=lambda item: item.relevance_score, reverse=True)
    if top_k is not None:
        return scored[:top_k]
    return scored


def _phrase_bonus(query_tokens: list[str], doc_tokens: list[str]) -> float:
    """Reward contiguous query-token sequences present in the document."""
    if len(query_tokens) < 2:
        return 1.0 if query_tokens and query_tokens[0] in doc_tokens else 0.0

    doc_set_bigrams = {
        (doc_tokens[i], doc_tokens[i + 1]) for i in range(len(doc_tokens) - 1)
    }
    query_bigrams = [
        (query_tokens[i], query_tokens[i + 1]) for i in range(len(query_tokens) - 1)
    ]
    if not query_bigrams:
        return 0.0
    hits = sum(1 for bigram in query_bigrams if bigram in doc_set_bigrams)
    return hits / len(query_bigrams)
