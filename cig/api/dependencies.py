"""
FastAPI dependency injection providers for CIG database adapters and search engines.
"""

from typing import Optional
from fastapi import Depends

from cig.storage.neo4j_adapter import Neo4jAdapter
from cig.retrieval.search import CodebaseSearchEngine

_neo4j_adapter_instance: Optional[Neo4jAdapter] = None
_search_engine_instance: Optional[CodebaseSearchEngine] = None


def get_neo4j_adapter() -> Neo4jAdapter:
    """
    Dependency provider for Neo4jAdapter.
    Returns a global/cached Neo4jAdapter instance.
    """
    global _neo4j_adapter_instance
    if _neo4j_adapter_instance is None:
        _neo4j_adapter_instance = Neo4jAdapter()
    return _neo4j_adapter_instance


def get_search_engine(
    adapter: Neo4jAdapter = Depends(get_neo4j_adapter),
) -> CodebaseSearchEngine:
    """
    Dependency provider for CodebaseSearchEngine.
    Injects the Neo4jAdapter dependency.
    """
    global _search_engine_instance
    if _search_engine_instance is None or _search_engine_instance.neo4j_adapter != adapter:
        _search_engine_instance = CodebaseSearchEngine(neo4j_adapter=adapter)
    return _search_engine_instance
