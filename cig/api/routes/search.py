"""
FastAPI router for natural language semantic code search queries.
"""

from fastapi import APIRouter, Depends

from cig.api.dependencies import get_search_engine
from cig.api.schemas import SearchRequest, SearchResponse
from cig.retrieval.search import CodebaseSearchEngine

router = APIRouter(prefix="/search", tags=["Search"])


@router.post(
    "",
    response_model=SearchResponse,
    summary="Natural language semantic search over codebase graph",
)
def search_codebase(
    request: SearchRequest,
    search_engine: CodebaseSearchEngine = Depends(get_search_engine),
) -> SearchResponse:
    """
    Search codebase symbols using UniXcoder vector similarity, filtered by optional intent or code smell criteria.
    """
    search_result = search_engine.search(
        query=request.query,
        top_k=request.top_k,
        intent_filter=request.intent_filter,
        smell_filter=request.smell_filter,
    )
    return SearchResponse(**search_result)
