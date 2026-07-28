"""
Graph Schema subpackage for CIG.

Defines Pydantic models for graph nodes, structural edges, model payloads (M1-M5),
and canonical taxonomies (Intent and Smell).
"""

from cig.graph_schema.contracts import (
    INTENT_TAXONOMY,
    SMELL_TAXONOMY,
    IntentCategory,
    M1CodeSummarizerOutput,
    M2DocScorerOutput,
    M3IntentClassifierOutput,
    M4SmellDetectorOutput,
    M5SemanticEdgeLabelerOutput,
    SmellCategory,
)
from cig.graph_schema.edges import (
    CallsEdge,
    ImportsEdge,
    InheritsEdge,
    InstantiatesEdge,
    SemanticEdgeAnnotation,
    StructuralEdge,
    StructuralEdgeType,
)
from cig.graph_schema.nodes import (
    BaseNode,
    ClassNode,
    FunctionNode,
    ModuleNode,
    NodeAnnotations,
    NodeType,
    SourceSpan,
)

__all__ = [
    # Taxonomies & Enums
    "INTENT_TAXONOMY",
    "SMELL_TAXONOMY",
    "IntentCategory",
    "SmellCategory",
    "NodeType",
    "StructuralEdgeType",
    # Contracts (M1-M5)
    "M1CodeSummarizerOutput",
    "M2DocScorerOutput",
    "M3IntentClassifierOutput",
    "M4SmellDetectorOutput",
    "M5SemanticEdgeLabelerOutput",
    # Nodes
    "SourceSpan",
    "NodeAnnotations",
    "BaseNode",
    "FunctionNode",
    "ClassNode",
    "ModuleNode",
    # Edges
    "SemanticEdgeAnnotation",
    "StructuralEdge",
    "CallsEdge",
    "ImportsEdge",
    "InheritsEdge",
    "InstantiatesEdge",
]
