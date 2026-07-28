"""
FastAPI router for graph exploration and impact analysis operations.
"""

from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status

from cig.api.dependencies import get_neo4j_adapter
from cig.api.schemas import (
    NodeListResponse,
    NodeDetailResponse,
    EdgeListResponse,
    ImpactAnalysisResponse,
)
from cig.storage.neo4j_adapter import Neo4jAdapter

router = APIRouter(tags=["Graph"])


@router.get(
    "/nodes",
    response_model=NodeListResponse,
    summary="List codebase symbol nodes",
)
def list_nodes(
    node_type: Optional[str] = Query(
        default=None, description="Optional node type filter ('function', 'class', 'module')"
    ),
    adapter: Neo4jAdapter = Depends(get_neo4j_adapter),
) -> NodeListResponse:
    """
    List symbol nodes from the knowledge graph, optionally filtered by node type.
    """
    nodes = adapter.list_nodes_by_type(node_type=node_type)
    return NodeListResponse(
        total=len(nodes),
        node_type=node_type,
        nodes=nodes,
    )


@router.get(
    "/edges",
    response_model=EdgeListResponse,
    summary="List codebase graph relationships",
)
def list_edges(
    edge_type: Optional[str] = Query(
        default=None, description="Optional edge type filter ('calls', 'imports', 'inherits', 'instantiates')"
    ),
    adapter: Neo4jAdapter = Depends(get_neo4j_adapter),
) -> EdgeListResponse:
    """
    List relationship edges from the knowledge graph, optionally filtered by edge type.
    """
    edges = adapter.list_edges_by_type(edge_type=edge_type)
    return EdgeListResponse(
        total=len(edges),
        edge_type=edge_type,
        edges=edges,
    )


@router.get(
    "/nodes/{node_id:path}/impact",
    response_model=ImpactAnalysisResponse,
    summary="Calculate downstream architectural impact of a target node",
)
def get_node_impact(
    node_id: str,
    max_hops: int = Query(default=3, ge=1, le=10, description="Maximum traversal depth/hops"),
    adapter: Neo4jAdapter = Depends(get_neo4j_adapter),
) -> ImpactAnalysisResponse:
    """
    Traverse the graph downstream up to max_hops from the target root node to assess architectural impact.
    """
    root_node = adapter.get_node_by_id(node_id)
    if root_node is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Root node '{node_id}' not found for impact analysis.",
        )

    downstream_nodes = adapter.get_impact_analysis(node_id=node_id, max_hops=max_hops)
    return ImpactAnalysisResponse(
        root_node_id=node_id,
        max_hops=max_hops,
        total_downstream=len(downstream_nodes),
        downstream_nodes=downstream_nodes,
    )


@router.get(
    "/nodes/{node_id:path}",
    response_model=NodeDetailResponse,
    summary="Get detailed node properties and annotations by ID",
)
def get_node_detail(
    node_id: str,
    adapter: Neo4jAdapter = Depends(get_neo4j_adapter),
) -> NodeDetailResponse:
    """
    Retrieve detailed AST properties, source location, and NLP annotations for a specific node.
    """
    node = adapter.get_node_by_id(node_id)
    if node is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Node '{node_id}' not found.",
        )
    return NodeDetailResponse(node=node)
