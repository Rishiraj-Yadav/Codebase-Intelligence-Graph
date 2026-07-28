"""
Typed payload contracts for model outputs (M1 through M5) and taxonomy definitions.
"""

from enum import Enum
from typing import Dict, List
from pydantic import BaseModel, Field


class IntentCategory(str, Enum):
    AUTHENTICATION = "authentication"
    DATA_PROCESSING = "data processing"
    API_COMMUNICATION = "API communication"
    BUSINESS_LOGIC = "business logic"
    DATABASE = "database"
    UI_RENDERING = "UI rendering"
    TESTING = "testing"
    CONFIGURATION = "configuration"
    ERROR_HANDLING = "error handling"
    CACHING = "caching"
    LOGGING = "logging"
    FILE_IO = "file I/O"
    MACHINE_LEARNING = "machine learning"
    MESSAGING = "messaging"
    UTILITY = "utility"


class SmellCategory(str, Enum):
    GOD_FUNCTION = "god function"
    MISLEADING_NAME = "misleading name"
    DEAD_CODE = "dead code"
    NAMING_INCONSISTENCY = "naming inconsistency"
    COMMENT_CODE_MISMATCH = "comment-code mismatch"


INTENT_TAXONOMY: List[str] = [e.value for e in IntentCategory]
SMELL_TAXONOMY: List[str] = [e.value for e in SmellCategory]


class M1CodeSummarizerOutput(BaseModel):
    """Payload contract for M1 (CodeT5 Summarizer)."""

    summary: str = Field(..., description="Generated natural language summary of the code snippet.")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Model confidence score between 0.0 and 1.0.")


class M2DocScorerOutput(BaseModel):
    """Payload contract for M2 (CodeBERT Doc Scorer)."""

    doc_quality_score: float = Field(
        ..., ge=0.0, le=1.0, description="Documentation quality score between 0.0 and 1.0."
    )
    doc_feedback: str = Field(..., description="Actionable feedback or docstring improvement suggestions.")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Model confidence score between 0.0 and 1.0.")


class M3IntentClassifierOutput(BaseModel):
    """Payload contract for M3 (CodeBERT Intent Classifier)."""

    intent_labels: List[IntentCategory] = Field(
        default_factory=list, description="Classified intent categories from Intent Taxonomy."
    )
    label_probabilities: Dict[str, float] = Field(
        default_factory=dict, description="Probabilities for each intent label."
    )
    confidence: float = Field(..., ge=0.0, le=1.0, description="Overall classification confidence score.")


class M4SmellDetectorOutput(BaseModel):
    """Payload contract for M4 (GraphCodeBERT Smell Detector)."""

    smell_labels: List[SmellCategory] = Field(
        default_factory=list, description="Detected code smell categories from Smell Taxonomy."
    )
    smell_probabilities: Dict[str, float] = Field(
        default_factory=dict, description="Probabilities for each smell label."
    )
    confidence: float = Field(..., ge=0.0, le=1.0, description="Overall smell detection confidence score.")


class M5SemanticEdgeLabelerOutput(BaseModel):
    """Payload contract for M5 (DeBERTa Semantic Edge Labeler)."""

    semantic_label: str = Field(..., description="High-level semantic relation label for the edge.")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Model confidence score between 0.0 and 1.0.")
    explanation: str = Field(..., description="Human-readable explanation for the predicted edge label.")
