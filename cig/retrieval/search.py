"""
Hybrid Semantic Search Engine combining UniXcoder/CodeBERT vector search (FAISS)
and graph storage node property retrieval (Neo4j).
"""

import logging
from typing import Any, Dict, List, Optional

from cig.retrieval.embedder import NodeEmbedder
from cig.retrieval.faiss_index import FAISSIndex
from cig.storage.neo4j_adapter import Neo4jAdapter

logger = logging.getLogger(__name__)


class CodebaseSearchEngine:
    """
    Codebase Search Engine orchestrating natural language query embedding,
    FAISS dense vector retrieval, and Neo4j enriched graph node details fetch.
    """

    def __init__(
        self,
        neo4j_adapter: Optional[Neo4jAdapter] = None,
        node_embedder: Optional[NodeEmbedder] = None,
        faiss_index: Optional[FAISSIndex] = None,
        faiss_index_path: Optional[str] = None,
    ) -> None:
        self.neo4j_adapter = neo4j_adapter or Neo4jAdapter()
        self.node_embedder = node_embedder or NodeEmbedder(use_mock_fallback=True)

        if faiss_index is not None:
            self.faiss_index = faiss_index
        elif faiss_index_path is not None:
            self.faiss_index = FAISSIndex.load(faiss_index_path)
        else:
            self.faiss_index = FAISSIndex()

    def search(self, query: str, top_k: int = 5) -> Dict[str, Any]:
        """
        Performs natural language semantic search across the codebase index.

        Args:
            query: Natural language search query string.
            top_k: Maximum number of search results to return.

        Returns:
            Dict[str, Any]: Structured search payload containing query, total_results, and results list.
        """
        if not query or not query.strip():
            return {
                "query": query,
                "total_results": 0,
                "results": [],
            }

        # 1. Embed search query into dense vector space
        query_vector = self.node_embedder.embed_code(query)

        # 2. Perform FAISS top-k vector similarity search
        hits = self.faiss_index.search(query_vector, top_k=top_k)

        # 3. Retrieve node metadata and annotations from Neo4j
        results: List[Dict[str, Any]] = []
        for hit in hits:
            node_id = hit["node_id"]
            score = hit["score"]
            node_details = self.neo4j_adapter.get_node_by_id(node_id)

            results.append(
                {
                    "node_id": node_id,
                    "score": round(float(score), 4),
                    "node": node_details or {"id": node_id},
                }
            )

        payload = {
            "query": query,
            "total_results": len(results),
            "results": results,
        }

        logger.info(f"Search query '{query}' returned {len(results)} results.")
        return payload
