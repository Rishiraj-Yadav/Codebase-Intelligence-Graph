"""
Pydantic models for AST nodes (Function, Class, Module) and node annotations.
"""

from enum import Enum
from typing import Dict, List, Literal, Optional
from pydantic import BaseModel, Field

from cig.graph_schema.contracts import (
    M1CodeSummarizerOutput,
    M2DocScorerOutput,
    M3IntentClassifierOutput,
    M4SmellDetectorOutput,
)


class NodeType(str, Enum):
    FUNCTION = "function"
    CLASS = "class"
    MODULE = "module"


class SourceSpan(BaseModel):
    """Source code location span."""

    start_line: int = Field(..., ge=1, description="1-indexed starting line number.")
    start_column: int = Field(..., ge=0, description="0-indexed starting column number.")
    end_line: int = Field(..., ge=1, description="1-indexed ending line number.")
    end_column: int = Field(..., ge=0, description="0-indexed ending column number.")


class NodeAnnotations(BaseModel):
    """
    NLP Model Annotations associated with a node.
    Keeps model predictions and explainability metadata distinct from AST structural facts.
    """

    summary: Optional[str] = Field(None, description="Natural language summary from M1.")
    summary_confidence: Optional[float] = Field(None, ge=0.0, le=1.0)

    doc_quality_score: Optional[float] = Field(None, ge=0.0, le=1.0, description="Doc quality score from M2.")
    doc_feedback: Optional[str] = Field(None, description="Doc feedback from M2.")
    doc_score_confidence: Optional[float] = Field(None, ge=0.0, le=1.0)

    intent_labels: List[str] = Field(default_factory=list, description="Classified intents from M3.")
    intent_confidence: Optional[float] = Field(None, ge=0.0, le=1.0)

    smell_labels: List[str] = Field(default_factory=list, description="Detected smells from M4.")
    smell_probabilities: Dict[str, float] = Field(default_factory=dict, description="Smell probabilities from M4.")
    smell_confidence: Optional[float] = Field(None, ge=0.0, le=1.0)

    def apply_m1(self, m1_output: M1CodeSummarizerOutput) -> None:
        """Apply M1 CodeT5 summarizer output payload."""
        self.summary = m1_output.summary
        self.summary_confidence = m1_output.confidence

    def apply_m2(self, m2_output: M2DocScorerOutput) -> None:
        """Apply M2 CodeBERT doc scorer output payload."""
        self.doc_quality_score = m2_output.doc_quality_score
        self.doc_feedback = m2_output.doc_feedback
        self.doc_score_confidence = m2_output.confidence

    def apply_m3(self, m3_output: M3IntentClassifierOutput) -> None:
        """Apply M3 CodeBERT intent classifier output payload."""
        self.intent_labels = [
            label.value if isinstance(label, Enum) else str(label) for label in m3_output.intent_labels
        ]
        self.intent_confidence = m3_output.confidence

    def apply_m4(self, m4_output: M4SmellDetectorOutput) -> None:
        """Apply M4 GraphCodeBERT smell detector output payload."""
        self.smell_labels = [
            label.value if isinstance(label, Enum) else str(label) for label in m4_output.smell_labels
        ]
        self.smell_probabilities = m4_output.smell_probabilities
        self.smell_confidence = m4_output.confidence


class BaseNode(BaseModel):
    """Base class for code graph nodes containing structural facts and annotation container."""

    id: str = Field(..., description="Stable unique identifier for the symbol node.")
    name: str = Field(..., description="Symbol name.")
    node_type: NodeType = Field(..., description="Canonical node type (function, class, module).")
    file_path: str = Field(..., description="File path relative to repository root.")
    source_span: SourceSpan = Field(..., description="Exact AST source code span.")
    docstring: Optional[str] = Field(None, description="Raw docstring extracted from source AST.")
    annotations: NodeAnnotations = Field(
        default_factory=NodeAnnotations, description="NLP model annotations (separate from structural facts)."
    )

    @property
    def summary(self) -> Optional[str]:
        return self.annotations.summary

    @property
    def doc_quality_score(self) -> Optional[float]:
        return self.annotations.doc_quality_score

    @property
    def doc_feedback(self) -> Optional[str]:
        return self.annotations.doc_feedback

    @property
    def intent_labels(self) -> List[str]:
        return self.annotations.intent_labels

    @property
    def smell_labels(self) -> List[str]:
        return self.annotations.smell_labels

    @property
    def smell_probabilities(self) -> Dict[str, float]:
        return self.annotations.smell_probabilities


class FunctionNode(BaseNode):
    """Function / Method symbol node."""

    node_type: Literal[NodeType.FUNCTION] = NodeType.FUNCTION
    signature: Optional[str] = Field(None, description="Full function signature.")
    parameters: List[str] = Field(default_factory=list, description="Function parameter names.")
    return_type: Optional[str] = Field(None, description="Return type annotation.")
    is_async: bool = Field(False, description="Whether the function is defined with async.")


class ClassNode(BaseNode):
    """Class symbol node."""

    node_type: Literal[NodeType.CLASS] = NodeType.CLASS
    base_classes: List[str] = Field(default_factory=list, description="Base class names or symbol IDs.")
    methods: List[str] = Field(default_factory=list, description="Method names or symbol IDs within class.")


class ModuleNode(BaseNode):
    """Module / File symbol node."""

    node_type: Literal[NodeType.MODULE] = NodeType.MODULE
    module_path: str = Field(..., description="Dot-separated python module path.")
    imported_modules: List[str] = Field(default_factory=list, description="Imported module names or paths.")
