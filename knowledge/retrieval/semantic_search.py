import time

from knowledge.index.vector_store import get_vector_store
from knowledge.ingestion.chunker import KnowledgeChunk
from knowledge.knowledge_store import get_knowledge_store
from knowledge.retrieval.keyword_search import keyword_search
from shared.schemas.knowledge import (
    KnowledgeDocument,
    KnowledgeSearchRequest,
    KnowledgeSearchResponse,
    SearchType,
)


def build_knowledge_index() -> int:
    store = get_knowledge_store()
    return get_vector_store().rebuild(store.all_chunks())


def search_knowledge(request: KnowledgeSearchRequest) -> KnowledgeSearchResponse:
    started = time.perf_counter()
    chunks = get_knowledge_store().all_chunks()

    if get_vector_store().count == 0 and chunks:
        get_vector_store().rebuild(chunks)

    if request.search_type == SearchType.KEYWORD:
        ranked = keyword_search(request.query, chunks, top_k=request.max_results)
    elif request.search_type == SearchType.SEMANTIC:
        ranked = _semantic_search(request.query, request.max_results)
    else:
        ranked = _hybrid_search(request.query, chunks, request.max_results)

    filtered = [
        item for item in ranked if item.relevance_score >= request.min_relevance_score
    ][: request.max_results]

    elapsed_ms = int((time.perf_counter() - started) * 1000)
    return KnowledgeSearchResponse(
        results=filtered,
        totalResults=len(filtered),
        searchType=request.search_type,
        executionTimeMs=elapsed_ms,
    )


def _semantic_search(query: str, top_k: int) -> list[KnowledgeDocument]:
    matches = get_vector_store().search(query, top_k=top_k)
    return [_match_to_document(match) for match in matches]


def _hybrid_search(query: str, chunks: list[KnowledgeChunk], top_k: int) -> list[KnowledgeDocument]:
    semantic = {doc.document_id: doc for doc in _semantic_search(query, top_k=top_k)}
    keyword = {doc.document_id: doc for doc in keyword_search(query, chunks)}

    merged_ids = list(dict.fromkeys([*semantic.keys(), *keyword.keys()]))
    merged: list[KnowledgeDocument] = []
    for chunk_id in merged_ids:
        sem = semantic.get(chunk_id)
        key = keyword.get(chunk_id)
        sem_score = sem.relevance_score if sem else 0.0
        key_score = key.relevance_score if key else 0.0
        base = sem or key
        if base is None:
            continue
        merged.append(
            KnowledgeDocument(
                document_id=base.document_id,
                title=base.title,
                excerpt=base.excerpt,
                relevance_score=round(min(1.0, sem_score * 0.7 + key_score * 0.3), 4),
                source=base.source,
            )
        )

    merged.sort(key=lambda item: item.relevance_score, reverse=True)
    return merged[:top_k]


def _match_to_document(match: dict) -> KnowledgeDocument:
    metadata = match.get("metadata", {})
    content = metadata.get("content", "")
    excerpt = content[:240] if isinstance(content, str) else ""
    return KnowledgeDocument(
        document_id=match["chunk_id"],
        title=str(metadata.get("section_header", "Knowledge chunk")),
        excerpt=excerpt,
        relevance_score=match["relevance_score"],
        source=str(metadata.get("source", "unknown")),
    )
