"""
Storage module for Codebase Intelligence Graph (CIG).
Exports Neo4j storage adapter, schema initializer, and Cypher query definitions.
"""

from cig.storage.neo4j_adapter import Neo4jAdapter
from cig.storage.schema_init import initialize_schema
from cig.storage.queries import (
    SCHEMA_STATEMENTS,
    UPSERT_NODE,
    FETCH_NODE_BY_ID,
    LIST_NODES_BY_TYPE,
    FILTER_NODES_BY_INTENT,
    FILTER_NODES_BY_SMELL,
    UPSERT_EDGE,
    LIST_EDGES_BY_TYPE,
    get_impact_analysis_query,
)

__all__ = [
    "Neo4jAdapter",
    "initialize_schema",
    "SCHEMA_STATEMENTS",
    "UPSERT_NODE",
    "FETCH_NODE_BY_ID",
    "LIST_NODES_BY_TYPE",
    "FILTER_NODES_BY_INTENT",
    "FILTER_NODES_BY_SMELL",
    "UPSERT_EDGE",
    "LIST_EDGES_BY_TYPE",
    "get_impact_analysis_query",
]
