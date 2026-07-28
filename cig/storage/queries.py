"""
Centralized Cypher query definitions and query builders for Neo4j persistence.
Contains schema setup statements, node/edge CRUD queries, intent/smell filtering,
and impact analysis graph traversals.
"""

from typing import List

# -----------------------------------------------------------------------------
# Schema Initializer Cypher Statements
# -----------------------------------------------------------------------------
SCHEMA_STATEMENTS: List[str] = [
    # Constraint: Unique node ID
    "CREATE CONSTRAINT node_id_unique IF NOT EXISTS FOR (n:Node) REQUIRE n.id IS UNIQUE",
    # Indexes: Node type and file path
    "CREATE INDEX node_type_idx IF NOT EXISTS FOR (n:Node) ON (n.node_type)",
    "CREATE INDEX node_file_path_idx IF NOT EXISTS FOR (n:Node) ON (n.file_path)",
    # Indexes: Node annotations
    "CREATE INDEX node_intent_labels_idx IF NOT EXISTS FOR (n:Node) ON (n.intent_labels)",
    "CREATE INDEX node_smell_labels_idx IF NOT EXISTS FOR (n:Node) ON (n.smell_labels)",
]

# -----------------------------------------------------------------------------
# Node Queries
# -----------------------------------------------------------------------------
UPSERT_NODE = """
MERGE (n:Node {id: $id})
SET n.name = $name,
    n.node_type = $node_type,
    n.file_path = $file_path,
    n.docstring = $docstring,
    n.start_line = $start_line,
    n.start_column = $start_column,
    n.end_line = $end_line,
    n.end_column = $end_column,
    n.signature = $signature,
    n.parameters = $parameters,
    n.return_type = $return_type,
    n.is_async = $is_async,
    n.base_classes = $base_classes,
    n.methods = $methods,
    n.module_path = $module_path,
    n.imported_modules = $imported_modules,
    n.summary = $summary,
    n.summary_confidence = $summary_confidence,
    n.doc_quality_score = $doc_quality_score,
    n.doc_feedback = $doc_feedback,
    n.doc_score_confidence = $doc_score_confidence,
    n.intent_labels = $intent_labels,
    n.intent_confidence = $intent_confidence,
    n.smell_labels = $smell_labels,
    n.smell_probabilities = $smell_probabilities,
    n.smell_confidence = $smell_confidence
RETURN n
"""

FETCH_NODE_BY_ID = """
MATCH (n:Node {id: $node_id})
RETURN n
"""

LIST_NODES_BY_TYPE = """
MATCH (n:Node {node_type: $node_type})
RETURN n
ORDER BY n.id ASC
"""

FILTER_NODES_BY_INTENT = """
MATCH (n:Node)
WHERE $intent IN n.intent_labels
RETURN n
ORDER BY n.id ASC
"""

FILTER_NODES_BY_SMELL = """
MATCH (n:Node)
WHERE $smell IN n.smell_labels
RETURN n
ORDER BY n.id ASC
"""

# -----------------------------------------------------------------------------
# Edge Queries
# -----------------------------------------------------------------------------
# Distinguishes structural edge properties (edge_type, id, source_id, target_id)
# from optional semantic annotation properties (semantic_label, semantic_confidence, semantic_explanation).
UPSERT_EDGE = """
MATCH (a:Node {id: $source_id})
MATCH (b:Node {id: $target_id})
MERGE (a)-[r:RELATIONSHIP {id: $id}]->(b)
SET r.edge_type = $edge_type,
    r.id = $id,
    r.source_id = $source_id,
    r.target_id = $target_id,
    r.semantic_label = $semantic_label,
    r.semantic_confidence = $semantic_confidence,
    r.semantic_explanation = $semantic_explanation
RETURN r
"""

LIST_EDGES_BY_TYPE = """
MATCH (a:Node)-[r]->(b:Node)
WHERE r.edge_type = $edge_type
RETURN r, a.id AS source_id, b.id AS target_id
ORDER BY r.id ASC
"""

# -----------------------------------------------------------------------------
# Impact Analysis Graph Traversal
# -----------------------------------------------------------------------------
def get_impact_analysis_query(max_hops: int = 3) -> str:
    """
    Generates a Cypher query returning all downstream nodes within N hops from a starting node.
    
    Args:
        max_hops: Maximum traversal depth (must be >= 1).
        
    Returns:
        Cypher query string.
    """
    if max_hops < 1:
        raise ValueError("max_hops must be at least 1")
    hops = int(max_hops)
    return f"""
MATCH (start:Node {{id: $node_id}})-[*1..{hops}]->(downstream:Node)
RETURN DISTINCT downstream
ORDER BY downstream.id ASC
"""
