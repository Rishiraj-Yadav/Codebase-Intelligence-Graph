"""
Neo4j Storage Adapter for persisting AST nodes and structural/semantic edges,
with querying, intent/smell filtering, impact analysis, and fallback/mock support.
"""

import json
import logging
from typing import Any, Dict, List, Optional, Union

try:
    import neo4j
    HAS_NEO4J = True
except ImportError:
    HAS_NEO4J = False

from cig.graph_schema.edges import (
    CallsEdge,
    ImportsEdge,
    InheritsEdge,
    InstantiatesEdge,
    StructuralEdge,
    StructuralEdgeType,
)
from cig.graph_schema.nodes import (
    BaseNode,
    ClassNode,
    FunctionNode,
    ModuleNode,
    NodeType,
)
from cig.parser.models import ParsedRepository
from cig.storage.queries import (
    FETCH_NODE_BY_ID,
    FILTER_NODES_BY_INTENT,
    FILTER_NODES_BY_SMELL,
    LIST_EDGES_BY_TYPE,
    LIST_NODES_BY_TYPE,
    UPSERT_EDGE,
    UPSERT_NODE,
    get_impact_analysis_query,
)

logger = logging.getLogger(__name__)


class Neo4jAdapter:
    """
    Neo4j Storage Adapter for Codebase Intelligence Graph (CIG).
    Handles node/edge persistence, Cypher querying, intent/smell filtering,
    and impact analysis traversal. Supports fallback/mock mode when Neo4j is offline.
    """

    def __init__(
        self,
        uri: str = "bolt://localhost:7687",
        auth: tuple = ("neo4j", "password"),
        database: str = "neo4j",
        driver: Any = None,
        fallback_mode: bool = False,
    ):
        self.uri = uri
        self.auth = auth
        self.database = database
        self.driver = driver
        self.in_fallback_mode = fallback_mode

        # In-memory store for fallback/mock mode
        self._memory_nodes: Dict[str, Dict[str, Any]] = {}
        self._memory_edges: Dict[str, Dict[str, Any]] = {}

        if not self.in_fallback_mode and self.driver is None:
            if not HAS_NEO4J:
                logger.info("neo4j library not available, switching to fallback mode.")
                self.in_fallback_mode = True
            else:
                try:
                    self.driver = neo4j.GraphDatabase.driver(self.uri, auth=self.auth)
                    self.driver.verify_connectivity()
                except Exception as e:
                    logger.warning(f"Could not connect to Neo4j at {uri}: {e}. Enabling fallback mode.")
                    self.in_fallback_mode = True
                    self.driver = None

    def is_connected(self) -> bool:
        """Returns True if connected to a live Neo4j instance."""
        if self.in_fallback_mode or self.driver is None:
            return False
        try:
            self.driver.verify_connectivity()
            return True
        except Exception:
            return False

    def close(self) -> None:
        """Close driver connection."""
        if self.driver is not None:
            try:
                self.driver.close()
            except Exception as e:
                logger.warning(f"Error closing Neo4j driver: {e}")

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

    def execute_query(
        self,
        query: str,
        parameters: Optional[Dict[str, Any]] = None,
        database: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """Executes a Cypher query against Neo4j or handles fallback mode."""
        if parameters is None:
            parameters = {}

        db = database or self.database

        if self.in_fallback_mode or self.driver is None:
            return self._execute_query_fallback(query, parameters)

        with self.driver.session(database=db) as session:
            result = session.run(query, parameters)
            records = []
            for record in result:
                record_dict = {}
                for key in record.keys():
                    val = record[key]
                    if hasattr(val, "_properties"):
                        record_dict[key] = dict(val._properties)
                    else:
                        record_dict[key] = val
                records.append(record_dict)
            return records

    def persist_repository(self, parsed_repo: ParsedRepository) -> int:
        """
        Persists all nodes and edges from a ParsedRepository into Neo4j graph storage.
        
        Returns:
            Number of nodes persisted.
        """
        persisted_nodes_count = 0

        # Persist Nodes
        for node in parsed_repo.nodes:
            node_dict = self._node_to_dict(node)
            if self.in_fallback_mode or self.driver is None:
                self._memory_nodes[node_dict["id"]] = node_dict
            else:
                self.execute_query(UPSERT_NODE, node_dict)
            persisted_nodes_count += 1

        # Persist Edges
        for edge in parsed_repo.edges:
            edge_dict = self._edge_to_dict(edge)
            if self.in_fallback_mode or self.driver is None:
                self._memory_edges[edge_dict["id"]] = edge_dict
            else:
                self.execute_query(UPSERT_EDGE, edge_dict)

        return persisted_nodes_count

    def get_node_by_id(self, node_id: str) -> Optional[Dict[str, Any]]:
        """Fetch node properties by unique node ID."""
        if self.in_fallback_mode or self.driver is None:
            return self._memory_nodes.get(node_id)

        records = self.execute_query(FETCH_NODE_BY_ID, {"node_id": node_id})
        if records and "n" in records[0]:
            return records[0]["n"]
        return None

    def list_nodes_by_type(self, node_type: Optional[Union[NodeType, str]] = None) -> List[Dict[str, Any]]:
        """List nodes matching node_type ('function', 'class', 'module') or all nodes if None."""
        if node_type is None:
            if self.in_fallback_mode or self.driver is None:
                return list(self._memory_nodes.values())
            records = self.execute_query("MATCH (n:Node) RETURN n")
            return [r["n"] for r in records if "n" in r]

        type_str = node_type.value if isinstance(node_type, NodeType) else str(node_type)
        if self.in_fallback_mode or self.driver is None:
            return [n for n in self._memory_nodes.values() if n.get("node_type") == type_str]

        records = self.execute_query(LIST_NODES_BY_TYPE, {"node_type": type_str})
        return [r["n"] for r in records if "n" in r]

    def list_edges_by_type(self, edge_type: Optional[Union[StructuralEdgeType, str]] = None) -> List[Dict[str, Any]]:
        """List edges matching edge_type ('calls', 'imports', 'inherits', 'instantiates') or all edges if None."""
        if edge_type is None:
            if self.in_fallback_mode or self.driver is None:
                return list(self._memory_edges.values())
            records = self.execute_query("MATCH (s:Node)-[r]->(t:Node) RETURN r, s.id AS source_id, t.id AS target_id")
            result = []
            for r in records:
                edge_data = r.get("r", {})
                if "source_id" in r and "source_id" not in edge_data:
                    edge_data["source_id"] = r["source_id"]
                if "target_id" in r and "target_id" not in edge_data:
                    edge_data["target_id"] = r["target_id"]
                result.append(edge_data)
            return result

        type_str = edge_type.value if isinstance(edge_type, StructuralEdgeType) else str(edge_type)
        if self.in_fallback_mode or self.driver is None:
            return [e for e in self._memory_edges.values() if e.get("edge_type") == type_str]

        records = self.execute_query(LIST_EDGES_BY_TYPE, {"edge_type": type_str})
        result = []
        for r in records:
            edge_data = r.get("r", {})
            if "source_id" in r and "source_id" not in edge_data:
                edge_data["source_id"] = r["source_id"]
            if "target_id" in r and "target_id" not in edge_data:
                edge_data["target_id"] = r["target_id"]
            result.append(edge_data)
        return result

    def filter_nodes_by_intent(self, intent: str) -> List[Dict[str, Any]]:
        """Filter nodes containing specific NLP intent label."""
        if self.in_fallback_mode or self.driver is None:
            return [
                n for n in self._memory_nodes.values()
                if intent in n.get("intent_labels", [])
            ]

        records = self.execute_query(FILTER_NODES_BY_INTENT, {"intent": intent})
        return [r["n"] for r in records if "n" in r]

    def filter_nodes_by_smell(self, smell: str) -> List[Dict[str, Any]]:
        """Filter nodes containing specific code smell label."""
        if self.in_fallback_mode or self.driver is None:
            return [
                n for n in self._memory_nodes.values()
                if smell in n.get("smell_labels", [])
            ]

        records = self.execute_query(FILTER_NODES_BY_SMELL, {"smell": smell})
        return [r["n"] for r in records if "n" in r]

    def get_impact_analysis(self, node_id: str, max_hops: int = 3) -> List[Dict[str, Any]]:
        """
        Impact analysis traversal returning all downstream nodes within N hops.
        
        Args:
            node_id: Starting root node ID.
            max_hops: Maximum traversal hops (>= 1).
            
        Returns:
            List of downstream node dictionaries.
        """
        if max_hops < 1:
            raise ValueError("max_hops must be at least 1")

        if self.in_fallback_mode or self.driver is None:
            return self._impact_analysis_fallback(node_id, max_hops)

        query = get_impact_analysis_query(max_hops=max_hops)
        records = self.execute_query(query, {"node_id": node_id})
        return [r["downstream"] for r in records if "downstream" in r]

    # -------------------------------------------------------------------------
    # Helper Conversion & Fallback Methods
    # -------------------------------------------------------------------------
    def _node_to_dict(self, node: BaseNode) -> Dict[str, Any]:
        """Converts BaseNode Pydantic model to Neo4j property dictionary."""
        node_type_str = node.node_type.value if isinstance(node.node_type, NodeType) else str(node.node_type)

        d: Dict[str, Any] = {
            "id": node.id,
            "name": node.name,
            "node_type": node_type_str,
            "file_path": node.file_path,
            "docstring": node.docstring or "",
            "start_line": node.source_span.start_line,
            "start_column": node.source_span.start_column,
            "end_line": node.source_span.end_line,
            "end_column": node.source_span.end_column,
            # Function specific
            "signature": getattr(node, "signature", None) or "",
            "parameters": getattr(node, "parameters", None) or [],
            "return_type": getattr(node, "return_type", None) or "",
            "is_async": getattr(node, "is_async", False),
            # Class specific
            "base_classes": getattr(node, "base_classes", None) or [],
            "methods": getattr(node, "methods", None) or [],
            # Module specific
            "module_path": getattr(node, "module_path", None) or "",
            "imported_modules": getattr(node, "imported_modules", None) or [],
            # Annotations
            "summary": node.annotations.summary or "",
            "summary_confidence": node.annotations.summary_confidence or 0.0,
            "doc_quality_score": node.annotations.doc_quality_score or 0.0,
            "doc_feedback": node.annotations.doc_feedback or "",
            "doc_score_confidence": node.annotations.doc_score_confidence or 0.0,
            "intent_labels": node.annotations.intent_labels or [],
            "intent_confidence": node.annotations.intent_confidence or 0.0,
            "smell_labels": node.annotations.smell_labels or [],
            "smell_probabilities": json.dumps(node.annotations.smell_probabilities or {}),
            "smell_confidence": node.annotations.smell_confidence or 0.0,
        }
        return d

    def _edge_to_dict(self, edge: StructuralEdge) -> Dict[str, Any]:
        """
        Converts StructuralEdge Pydantic model to Neo4j property dictionary.
        Distinguishes structural properties (edge_type, id, source_id, target_id)
        from semantic annotation properties (semantic_label, semantic_confidence, semantic_explanation).
        """
        edge_type_str = edge.edge_type.value if isinstance(edge.edge_type, StructuralEdgeType) else str(edge.edge_type)

        d: Dict[str, Any] = {
            "id": edge.id,
            "source_id": edge.source_id,
            "target_id": edge.target_id,
            "edge_type": edge_type_str,
            # Semantic annotation properties
            "semantic_label": edge.annotations.label if edge.annotations else "",
            "semantic_confidence": edge.annotations.confidence if edge.annotations else 0.0,
            "semantic_explanation": edge.annotations.explanation if edge.annotations else "",
        }
        return d

    def _impact_analysis_fallback(self, start_node_id: str, max_hops: int) -> List[Dict[str, Any]]:
        """In-memory BFS traversal for impact analysis fallback."""
        if start_node_id not in self._memory_nodes:
            return []

        visited_ids = set()
        queue = [(start_node_id, 0)]
        result_nodes = []

        while queue:
            curr_id, depth = queue.pop(0)
            if depth >= max_hops:
                continue

            # Find all outgoing edges from curr_id
            for edge in self._memory_edges.values():
                if edge["source_id"] == curr_id:
                    target_id = edge["target_id"]
                    if target_id not in visited_ids and target_id in self._memory_nodes:
                        visited_ids.add(target_id)
                        result_nodes.append(self._memory_nodes[target_id])
                        queue.append((target_id, depth + 1))

        return result_nodes

    def _execute_query_fallback(
        self, query: str, parameters: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Basic Cypher pattern emulator for fallback mode."""
        if "MATCH (n:Node {id: $node_id})" in query:
            node_id = parameters.get("node_id")
            node = self._memory_nodes.get(node_id)
            return [{"n": node}] if node else []

        if "MATCH (n:Node {node_type: $node_type})" in query:
            n_type = parameters.get("node_type")
            return [{"n": n} for n in self._memory_nodes.values() if n.get("node_type") == n_type]

        if "WHERE $intent IN n.intent_labels" in query:
            intent = parameters.get("intent")
            return [
                {"n": n} for n in self._memory_nodes.values()
                if intent in n.get("intent_labels", [])
            ]

        if "WHERE $smell IN n.smell_labels" in query:
            smell = parameters.get("smell")
            return [
                {"n": n} for n in self._memory_nodes.values()
                if smell in n.get("smell_labels", [])
            ]

        if "WHERE r.edge_type = $edge_type" in query:
            e_type = parameters.get("edge_type")
            edges = [e for e in self._memory_edges.values() if e.get("edge_type") == e_type]
            return [{"r": e, "source_id": e["source_id"], "target_id": e["target_id"]} for e in edges]

        return []
