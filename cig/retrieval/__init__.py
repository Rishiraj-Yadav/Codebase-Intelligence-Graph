"""
FAISS Retrieval and Embedding Layer for CIG (Phase 5).
Exports NodeEmbedder, FAISSIndex, and CodebaseSearchEngine.
"""

from cig.retrieval.embedder import NodeEmbedder
from cig.retrieval.faiss_index import FAISSIndex
from cig.retrieval.search import CodebaseSearchEngine

__all__ = [
    "NodeEmbedder",
    "FAISSIndex",
    "CodebaseSearchEngine",
]
