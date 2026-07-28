"""
Model interfaces and mock implementations for Codebase Intelligence Graph (CIG).
"""

from cig.models.m1_summarizer import CodeT5Summarizer
from cig.models.m2_doc_scorer import CodeBERTDocScorer
from cig.models.m3_intent_classifier import CodeBERTIntentClassifier
from cig.models.m4_smell_detector import GraphCodeBERTSmellDetector
from cig.models.m5_edge_labeler import DeBERTaEdgeLabeler
from cig.models.mock_models import (
    MockM1Summarizer,
    MockM2DocScorer,
    MockM3IntentClassifier,
    MockM4SmellDetector,
    MockM5EdgeLabeler,
    MockModelPipeline,
)

__all__ = [
    "CodeT5Summarizer",
    "CodeBERTDocScorer",
    "CodeBERTIntentClassifier",
    "GraphCodeBERTSmellDetector",
    "DeBERTaEdgeLabeler",
    "MockM1Summarizer",
    "MockM2DocScorer",
    "MockM3IntentClassifier",
    "MockM4SmellDetector",
    "MockM5EdgeLabeler",
    "MockModelPipeline",
]
