"""
Pydantic models for structural edges and semantic edge annotations.
"""

from enum import Enum
from typing import Literal, Optional
from pydantic import BaseModel, Field


class StructuralEdgeType(str, Enum):
    CALLS = "calls"
    IMPORTS = "imports"
    INHERITS = "inherits"
    INSTANTIATES = "instantiates"


class SemanticEdgeAnnotation(BaseModel):
    """Semantic annotation associated with an edge (M5 DeBERTa output)."""

    label: str = Field(..., description="High-level semantic relation label.")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Model confidence score between 0.0 and 1.0.")
    explanation: str = Field(..., description="Human-readable explanation of why this edge relation exists.")


class StructuralEdge(BaseModel):
    """Base class for directed structural graph edges between symbol nodes."""

    id: str = Field(..., description="Unique edge identifier.")
    source_id: str = Field(..., description="Source node symbol ID.")
    target_id: str = Field(..., description="Target node symbol ID.")
    edge_type: StructuralEdgeType = Field(..., description="Structural relation type.")
    annotations: Optional[SemanticEdgeAnnotation] = Field(
        None, description="Optional M5 semantic edge annotation."
    )


class CallsEdge(StructuralEdge):
    """Calls structural edge representing function/method call invocation."""

    edge_type: Literal[StructuralEdgeType.CALLS] = StructuralEdgeType.CALLS


class ImportsEdge(StructuralEdge):
    """Imports structural edge representing module or symbol import dependency."""

    edge_type: Literal[StructuralEdgeType.IMPORTS] = StructuralEdgeType.IMPORTS


class InheritsEdge(StructuralEdge):
    """Inherits structural edge representing class inheritance relation."""

    edge_type: Literal[StructuralEdgeType.INHERITS] = StructuralEdgeType.INHERITS


class InstantiatesEdge(StructuralEdge):
    """Instantiates structural edge representing object instantiation of a class."""

    edge_type: Literal[StructuralEdgeType.INSTANTIATES] = StructuralEdgeType.INSTANTIATES
