from enum import Enum

from pydantic import Field

from shared.schemas.common import AliasModel


class SearchType(str, Enum):
    SEMANTIC = "SEMANTIC"
    KEYWORD = "KEYWORD"
    HYBRID = "HYBRID"


class KnowledgeSearchRequest(AliasModel):
    query: str = Field(..., min_length=1, max_length=500)
    search_type: SearchType = Field(default=SearchType.HYBRID, alias="searchType")
    max_results: int = Field(default=5, ge=1, le=10, alias="maxResults")
    min_relevance_score: float = Field(default=0.75, ge=0.0, le=1.0, alias="minRelevanceScore")


class KnowledgeDocument(AliasModel):
    document_id: str = Field(..., alias="documentId")
    title: str
    excerpt: str
    relevance_score: float = Field(..., alias="relevanceScore")
    source: str


class KnowledgeSearchResponse(AliasModel):
    results: list[KnowledgeDocument]
    total_results: int = Field(alias="totalResults")
    search_type: SearchType = Field(alias="searchType")
    execution_time_ms: int = Field(alias="executionTimeMs")
