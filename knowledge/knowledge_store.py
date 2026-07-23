from knowledge.ingestion.chunker import KnowledgeChunk, chunk_documents
from knowledge.ingestion.loader import LoadedDocument, load_markdown_sources


class KnowledgeStore:
    """Loads markdown sources and exposes header-aware contextual chunks."""

    def __init__(
        self,
        documents: list[LoadedDocument] | None = None,
        chunks: list[KnowledgeChunk] | None = None,
    ) -> None:
        self._documents = documents if documents is not None else load_markdown_sources()
        self._chunks = chunks if chunks is not None else chunk_documents(self._documents)

    def all_documents(self) -> list[LoadedDocument]:
        return list(self._documents)

    def all_chunks(self) -> list[KnowledgeChunk]:
        return list(self._chunks)

    def get_document(self, document_id: str) -> LoadedDocument | None:
        return next((doc for doc in self._documents if doc.document_id == document_id), None)

    def get_chunk(self, chunk_id: str) -> KnowledgeChunk | None:
        return next((chunk for chunk in self._chunks if chunk.chunk_id == chunk_id), None)

    def chunks_for_document(self, document_id: str) -> list[KnowledgeChunk]:
        return [chunk for chunk in self._chunks if chunk.document_id == document_id]

    def reload(self) -> None:
        self._documents = load_markdown_sources()
        self._chunks = chunk_documents(self._documents)


_store: KnowledgeStore | None = None


def get_knowledge_store() -> KnowledgeStore:
    global _store
    if _store is None:
        _store = KnowledgeStore()
    return _store
