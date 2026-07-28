"""
Pydantic API request and response schemas for Codebase Intelligence Graph (CIG).

Defines explicit typed models for:
- Asynchronous Ingestion APIs (IngestRequest, IngestResponse, JobStatusResponse)
- Graph Exploration Read APIs (NodeListResponse, NodeDetailResponse, EdgeListResponse, ImpactAnalysisResponse)
- Code Search Read APIs (SearchRequest, SearchResultItem, SearchResponse)
- Annotation and Provenance models (exposing confidence, file_path, source_span, and evidence)
"""

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


# ============================================================================
# Provenance and Annotation Schemas
# ============================================================================

class SourceSpan(BaseModel):
    """Source code location span within a file."""

    start_line: int = Field(..., ge=1, description="1-indexed starting line number.")
    start_column: int = Field(..., ge=0, description="0-indexed starting column number.")
    end_line: int = Field(..., ge=1, description="1-indexed ending line number.")
    end_column: int = Field(..., ge=0, description="0-indexed ending column number.")


class Provenance(BaseModel):
    """Exact source location and file path provenance metadata for graph entities and annotations."""

    file_path: str = Field(..., description="File path relative to repository root.")
    source_span: SourceSpan = Field(..., description="Exact source code line and column span.")


class AnnotationOutput(BaseModel):
    """
    Explicit model annotation payload enforcing system rules:
    - Must include confidence score (0.0 to 1.0).
    - Must include exact provenance fields (file_path, source_span).
    - Must include model evidence (explanation, snippet, or rationale).
    """

    annotation_type: str = Field(
        ..., description="Type of annotation (e.g., 'summary', 'doc_score', 'intent', 'smell', 'semantic_edge')."
    )
    value: Any = Field(..., description="Prediction or value assigned by the model.")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Model confidence score between 0.0 and 1.0.")
    file_path: str = Field(..., description="File path relative to repository root.")
    source_span: SourceSpan = Field(..., description="Exact AST source code span.")
    evidence: Optional[str] = Field(
        default=None, description="Supporting evidence, code snippet, or model explanation rationale."
    )


# ============================================================================
# Asynchronous Ingestion Schemas
# ============================================================================

class IngestRequest(BaseModel):
    """Request model for starting asynchronous repository ingestion."""

    repo_path: str = Field(..., description="Absolute or relative file path to local repository.")
    ignore_patterns: Optional[List[str]] = Field(
        default=None, description="Optional glob patterns to ignore during scanning."
    )


class IngestResponse(BaseModel):
    """Response model after initiating asynchronous repository ingestion."""

    job_id: str = Field(..., description="Unique Celery/background job identifier.")
    status: str = Field(..., description="Initial job status (e.g. 'queued', 'processing').")
    message: str = Field(..., description="Human-readable status summary message.")


class JobStatusResponse(BaseModel):
    """Response model for querying asynchronous ingestion job status."""

    job_id: str = Field(..., description="Unique job identifier.")
    status: str = Field(..., description="Current job execution status ('PENDING', 'STARTED', 'SUCCESS', 'FAILURE').")
    result: Optional[Dict[str, Any]] = Field(
        default=None, description="Ingestion execution summary/result metrics if job completed successfully."
    )
    error: Optional[str] = Field(
        default=None, description="Detailed error message if job execution failed."
    )


# ============================================================================
# Graph Exploration Read Schemas
# ============================================================================

class NodeListResponse(BaseModel):
    """Response model for listing graph symbol nodes."""

    total: int = Field(..., ge=0, description="Total count of nodes matching query filters.")
    node_type: Optional[str] = Field(
        default=None, description="Optional node type filter applied ('function', 'class', 'module')."
    )
    nodes: List[Dict[str, Any]] = Field(
        default_factory=list, description="List of node payloads containing AST attributes and annotations."
    )


class NodeDetailResponse(BaseModel):
    """Response model for single node detailed query."""

    node: Dict[str, Any] = Field(
        ..., description="Detailed node dictionary containing attributes, annotations, and provenance."
    )


class EdgeListResponse(BaseModel):
    """Response model for listing graph relationships/edges."""

    total: int = Field(..., ge=0, description="Total count of edges matching query filters.")
    edge_type: Optional[str] = Field(
        default=None, description="Optional edge type filter applied ('CALLS', 'DEFINED_IN', etc.)."
    )
    edges: List[Dict[str, Any]] = Field(
        default_factory=list, description="List of edge payloads including source, target, type, and annotations."
    )


class ImpactAnalysisResponse(BaseModel):
    """Response model for downstream architectural impact analysis traversal."""

    root_node_id: str = Field(..., description="ID of the target root node analyzed for impact.")
    max_hops: int = Field(..., ge=1, description="Maximum traversal depth/hops specified for impact calculation.")
    total_downstream: int = Field(..., ge=0, description="Total count of unique downstream impacted nodes found.")
    downstream_nodes: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="List of downstream impacted node payloads with distance, path, and node details.",
    )


# ============================================================================
# Code Search Read Schemas
# ============================================================================

class SearchRequest(BaseModel):
    """Request model for natural language semantic code search."""

    query: str = Field(..., min_length=1, description="Natural language search query.")
    top_k: int = Field(default=5, ge=1, le=100, description="Maximum number of search results to return.")
    intent_filter: Optional[str] = Field(
        default=None, description="Optional intent category filter (e.g., 'authentication', 'database')."
    )
    smell_filter: Optional[str] = Field(
        default=None, description="Optional code smell filter (e.g., 'god function', 'dead code')."
    )


class SearchResultItem(BaseModel):
    """Individual search result item with score, ID, and node metadata."""

    node_id: str = Field(..., description="Unique symbol node ID.")
    score: float = Field(..., description="Semantic search relevance score.")
    node: Dict[str, Any] = Field(
        ..., description="Node dictionary including symbol metadata, provenance, and annotations."
    )


class SearchResponse(BaseModel):
    """Response model for natural language semantic code search query."""

    query: str = Field(..., description="Original search query string.")
    total_results: int = Field(..., ge=0, description="Total count of matching search results returned.")
    results: List[SearchResultItem] = Field(
        default_factory=list, description="Ranked list of search result items."
    )
