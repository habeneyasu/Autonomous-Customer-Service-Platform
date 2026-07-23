import chromadb
from chromadb.utils.embedding_functions import DefaultEmbeddingFunction

from knowledge.index import COLLECTION_NAME, get_index_path
from knowledge.ingestion.chunker import KnowledgeChunk


class KnowledgeVectorStore:
    """Persistent ChromaDB index for contextual knowledge chunks."""

    def __init__(self) -> None:
        self._client = chromadb.PersistentClient(path=str(get_index_path()))
        self._embedding = DefaultEmbeddingFunction()
        self._collection = self._client.get_or_create_collection(
            name=COLLECTION_NAME,
            embedding_function=self._embedding,
            metadata={"hnsw:space": "cosine"},
        )

    @property
    def count(self) -> int:
        return self._collection.count()

    def rebuild(self, chunks: list[KnowledgeChunk]) -> int:
        self._client.delete_collection(COLLECTION_NAME)
        self._collection = self._client.get_or_create_collection(
            name=COLLECTION_NAME,
            embedding_function=self._embedding,
            metadata={"hnsw:space": "cosine"},
        )
        if not chunks:
            return 0

        self._collection.add(
            ids=[chunk.chunk_id for chunk in chunks],
            documents=[chunk.contextual_text for chunk in chunks],
            metadatas=[_chunk_metadata(chunk) for chunk in chunks],
        )
        return len(chunks)

    def search(self, query: str, *, top_k: int = 5) -> list[dict]:
        if self._collection.count() == 0:
            return []

        result = self._collection.query(
            query_texts=[query],
            n_results=min(top_k, self._collection.count()),
            include=["documents", "metadatas", "distances"],
        )

        ids = result.get("ids", [[]])[0]
        documents = result.get("documents", [[]])[0]
        metadatas = result.get("metadatas", [[]])[0]
        distances = result.get("distances", [[]])[0]

        matches: list[dict] = []
        for chunk_id, document, metadata, distance in zip(ids, documents, metadatas, distances, strict=True):
            matches.append(
                {
                    "chunk_id": chunk_id,
                    "document": document,
                    "metadata": metadata or {},
                    "distance": float(distance),
                    "relevance_score": _distance_to_score(float(distance)),
                }
            )
        return matches


def _chunk_metadata(chunk: KnowledgeChunk) -> dict[str, str | int | float]:
    return {
        "document_id": chunk.document_id,
        "document_title": chunk.document_title,
        "parent_header": chunk.parent_header,
        "section_header": chunk.section_header,
        "header_level": chunk.header_level,
        "source": chunk.source,
        "source_file": chunk.source_file,
        "topic": chunk.topic,
        "tags": ",".join(chunk.tags),
        "content": chunk.content,
    }


def _distance_to_score(distance: float) -> float:
    return round(max(0.0, 1.0 - distance), 4)


_vector_store: KnowledgeVectorStore | None = None


def get_vector_store() -> KnowledgeVectorStore:
    global _vector_store
    if _vector_store is None:
        _vector_store = KnowledgeVectorStore()
    return _vector_store
