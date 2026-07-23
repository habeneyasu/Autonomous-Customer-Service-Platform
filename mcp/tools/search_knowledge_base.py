from typing import Any

from knowledge.retrieval.semantic_search import search_knowledge
from shared.schemas.knowledge import KnowledgeSearchRequest
from shared.schemas.mcp import CustomerContext


class SearchKnowledgeBaseTool:
    name = "search_knowledge_base"
    description = (
        "Search the verified business knowledge base using semantic, keyword, or hybrid retrieval."
    )
    state_modifying = False
    authorized_intents = ["GENERAL_INQUIRY"]

    def run(
        self,
        parameters: dict[str, Any],
        customer_context: CustomerContext | None = None,
    ) -> dict[str, Any]:
        _ = customer_context
        request = KnowledgeSearchRequest.model_validate(parameters)
        return search_knowledge(request).model_dump(by_alias=True)
