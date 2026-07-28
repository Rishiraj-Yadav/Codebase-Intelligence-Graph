"""
Deterministic mock implementations for model interfaces M1 through M5.
Fast, offline, zero-dependency mocks for testing and development.
"""

import hashlib
import re
from typing import Dict, List, Optional, Tuple, Any

from pydantic import BaseModel
from cig.graph_schema.contracts import (
    M1CodeSummarizerOutput,
    M2DocScorerOutput,
    M3IntentClassifierOutput,
    M4SmellDetectorOutput,
    M5SemanticEdgeLabelerOutput,
    IntentCategory,
    SmellCategory,
    INTENT_TAXONOMY,
    SMELL_TAXONOMY,
)


def _hash_code(code: str) -> int:
    """Helper to generate a deterministic integer hash from a code string."""
    clean_code = code.strip()
    if not clean_code:
        return 0
    digest = hashlib.sha256(clean_code.encode("utf-8")).hexdigest()
    return int(digest[:8], 16)


class MockM1Summarizer:
    """Deterministic mock for M1 CodeT5 Summarizer."""

    def predict(self, code: str) -> M1CodeSummarizerOutput:
        summary, output = self.summarize(code)
        return output

    def summarize(self, code: str) -> Tuple[str, M1CodeSummarizerOutput]:
        clean_code = code.strip()
        if not clean_code:
            summary = "Empty code snippet provided."
            out = M1CodeSummarizerOutput(summary=summary, confidence=0.0)
            return summary, out

        func_match = re.search(r"def\s+([a-zA-Z0-9_]+)", clean_code)
        class_match = re.search(r"class\s+([a-zA-Z0-9_]+)", clean_code)

        if func_match:
            name = func_match.group(1).replace("_", " ")
            summary = f"Function that performs {name} operations."
        elif class_match:
            name = class_match.group(1).replace("_", " ")
            summary = f"Class representing {name} entity."
        else:
            summary = "Code snippet executing general logic."

        h = _hash_code(clean_code)
        confidence = round(0.70 + (h % 25) / 100.0, 2)
        out = M1CodeSummarizerOutput(summary=summary, confidence=confidence)
        return summary, out


class MockM2DocScorer:
    """Deterministic mock for M2 CodeBERT Doc Scorer."""

    def predict(self, code: str, docstring: Optional[str] = None) -> M2DocScorerOutput:
        score_100, issues, output = self.score_docstring(code, docstring)
        return output

    def score_docstring(
        self, code: str, docstring: Optional[str] = None
    ) -> Tuple[float, List[str], M2DocScorerOutput]:
        clean_code = code.strip()
        issues: List[str] = []

        if not docstring or not docstring.strip():
            doc_quality_score = 0.20
            score_100 = 20.0
            issues.append("Docstring is missing.")
            doc_feedback = "Add a comprehensive docstring describing function purpose, parameters, and return value."
            confidence = 1.0
        else:
            clean_doc = docstring.strip()
            score_acc = 0.50
            if len(clean_doc) > 20:
                score_acc += 0.20
            if "return" in clean_doc.lower() or "returns" in clean_doc.lower():
                score_acc += 0.15
            if "param" in clean_doc.lower() or "args" in clean_doc.lower() or ":" in clean_doc:
                score_acc += 0.10

            h = _hash_code(clean_code + clean_doc)
            variance = ((h % 10) - 5) / 100.0
            doc_quality_score = max(0.0, min(1.0, score_acc + variance))
            score_100 = round(doc_quality_score * 100, 2)

            if doc_quality_score < 0.6:
                issues.append("Docstring lacks detailed parameter or return descriptions.")
                doc_feedback = "Improve docstring by adding parameter and return type details."
            else:
                doc_feedback = "Docstring is clear and informative."

            confidence = round(0.80 + (h % 15) / 100.0, 2)

        out = M2DocScorerOutput(
            doc_quality_score=round(doc_quality_score, 2),
            doc_feedback=doc_feedback,
            confidence=confidence,
        )
        return score_100, issues, out


class MockM3IntentClassifier:
    """Deterministic mock for M3 CodeBERT Intent Classifier."""

    def __init__(self, threshold: float = 0.5):
        self.threshold = threshold

    def predict(self, code: str) -> M3IntentClassifierOutput:
        intents, probs, output = self.classify(code)
        return output

    def classify(
        self, code: str
    ) -> Tuple[List[IntentCategory], Dict[str, float], M3IntentClassifierOutput]:
        clean_code = code.strip()
        probs: Dict[str, float] = {cat.value: 0.05 for cat in IntentCategory}

        if not clean_code:
            out = M3IntentClassifierOutput(
                intent_labels=[],
                label_probabilities=probs,
                confidence=0.0,
            )
            return [], probs, out

        code_lower = clean_code.lower()
        h = _hash_code(clean_code)

        if any(kw in code_lower for kw in ["auth", "login", "password", "token", "jwt", "user"]):
            probs[IntentCategory.AUTHENTICATION.value] = 0.90
        if any(kw in code_lower for kw in ["db", "query", "sql", "filter", "session", "execute"]):
            probs[IntentCategory.DATABASE.value] = 0.85
        if any(kw in code_lower for kw in ["calculate", "metric", "data", "transform", "process", "map"]):
            probs[IntentCategory.DATA_PROCESSING.value] = 0.80
        if any(kw in code_lower for kw in ["test", "assert", "mock"]):
            probs[IntentCategory.TESTING.value] = 0.88
        if any(kw in code_lower for kw in ["http", "request", "api", "fetch", "client"]):
            probs[IntentCategory.API_COMMUNICATION.value] = 0.85
        if any(kw in code_lower for kw in ["try", "except", "raise", "error"]):
            probs[IntentCategory.ERROR_HANDLING.value] = 0.75
        if any(kw in code_lower for kw in ["file", "read", "write", "open", "path"]):
            probs[IntentCategory.FILE_IO.value] = 0.80
        if any(kw in code_lower for kw in ["log", "logger", "info", "debug", "warning"]):
            probs[IntentCategory.LOGGING.value] = 0.82
        if any(kw in code_lower for kw in ["ui", "render", "component", "html", "view"]):
            probs[IntentCategory.UI_RENDERING.value] = 0.84
        if any(kw in code_lower for kw in ["config", "settings", "env", "setup"]):
            probs[IntentCategory.CONFIGURATION.value] = 0.86
        if any(kw in code_lower for kw in ["cache", "redis", "ttl", "memcached"]):
            probs[IntentCategory.CACHING.value] = 0.83
        if any(kw in code_lower for kw in ["model", "train", "predict", "loss", "torch"]):
            probs[IntentCategory.MACHINE_LEARNING.value] = 0.89
        if any(kw in code_lower for kw in ["message", "queue", "kafka", "mq", "publish"]):
            probs[IntentCategory.MESSAGING.value] = 0.87
        if any(kw in code_lower for kw in ["business", "rule", "discount", "order", "price"]):
            probs[IntentCategory.BUSINESS_LOGIC.value] = 0.81
        if any(kw in code_lower for kw in ["utility", "util", "helper", "slugify"]):
            probs[IntentCategory.UTILITY.value] = 0.79

        selected_labels: List[IntentCategory] = [
            IntentCategory(cat) for cat, p in probs.items() if p >= self.threshold
        ]

        overall_conf = round(max(probs.values()), 2)
        out = M3IntentClassifierOutput(
            intent_labels=selected_labels,
            label_probabilities={k: round(v, 2) for k, v in probs.items()},
            confidence=overall_conf,
        )
        return selected_labels, probs, out


class MockM4SmellDetector:
    """Deterministic mock for M4 GraphCodeBERT Smell Detector."""

    def __init__(self, threshold: float = 0.5):
        self.threshold = threshold

    def predict(self, code: str) -> M4SmellDetectorOutput:
        probs, output = self.detect_smells(code)
        return output

    def detect_smells(self, code: str) -> Tuple[Dict[str, float], M4SmellDetectorOutput]:
        clean_code = code.strip()
        probs: Dict[str, float] = {smell.value: 0.05 for smell in SmellCategory}

        if not clean_code:
            out = M4SmellDetectorOutput(
                smell_labels=[],
                smell_probabilities=probs,
                confidence=0.0,
            )
            return probs, out

        lines = clean_code.splitlines()
        h = _hash_code(clean_code)

        if len(lines) > 30:
            probs[SmellCategory.GOD_FUNCTION.value] = 0.85
        if "temp" in clean_code or "data_stuff" in clean_code or "do_thing" in clean_code:
            probs[SmellCategory.MISLEADING_NAME.value] = 0.75
        if "if False:" in clean_code or "pass  # dead" in clean_code:
            probs[SmellCategory.DEAD_CODE.value] = 0.90
        if re.search(r"[a-z]+[A-Z]", clean_code) and "_" in clean_code:
            probs[SmellCategory.NAMING_INCONSISTENCY.value] = 0.70
        if "#" in clean_code and "TODO" in clean_code:
            probs[SmellCategory.COMMENT_CODE_MISMATCH.value] = 0.65

        selected_smells: List[SmellCategory] = [
            SmellCategory(smell) for smell, p in probs.items() if p >= self.threshold
        ]

        overall_conf = round(max(probs.values()), 2)
        out = M4SmellDetectorOutput(
            smell_labels=selected_smells,
            smell_probabilities={k: round(v, 2) for k, v in probs.items()},
            confidence=overall_conf,
        )
        return probs, out


class MockM5EdgeLabeler:
    """Deterministic mock for M5 DeBERTa Cross-Encoder Edge Labeler."""

    def predict(
        self,
        source_code: str,
        target_code: str,
        source_summary: Optional[str] = None,
        target_summary: Optional[str] = None,
    ) -> M5SemanticEdgeLabelerOutput:
        label, conf, exp, output = self.label_edge(
            source_code, target_code, source_summary, target_summary
        )
        return output

    def label_edge(
        self,
        source_code: str,
        target_code: str,
        source_summary: Optional[str] = None,
        target_summary: Optional[str] = None,
    ) -> Tuple[str, float, str, M5SemanticEdgeLabelerOutput]:
        clean_src = source_code.strip()
        clean_tgt = target_code.strip()

        if not clean_src or not clean_tgt:
            out = M5SemanticEdgeLabelerOutput(
                semantic_label="UNKNOWN",
                confidence=0.0,
                explanation="Empty code input provided for source or target.",
            )
            return "UNKNOWN", 0.0, out.explanation, out

        src_func = re.search(r"def\s+([a-zA-Z0-9_]+)", clean_src)
        tgt_func = re.search(r"def\s+([a-zA-Z0-9_]+)", clean_tgt)

        src_name = src_func.group(1) if src_func else "source"
        tgt_name = tgt_func.group(1) if tgt_func else "target"

        if tgt_name in clean_src:
            label = "CALLS"
            explanation = f"Source function '{src_name}' directly invokes target function '{tgt_name}'."
            conf = 0.92
        elif "db" in clean_src and "db" in clean_tgt:
            label = "DATA_FLOW"
            explanation = f"Functions '{src_name}' and '{tgt_name}' share database data context."
            conf = 0.81
        else:
            h = _hash_code(clean_src + clean_tgt)
            if h % 3 == 0:
                label = "DEPENDS_ON"
                explanation = f"Functional dependency detected between '{src_name}' and '{tgt_name}'."
            elif h % 3 == 1:
                label = "HELPER_OF"
                explanation = f"Target function '{tgt_name}' provides utility support for '{src_name}'."
            else:
                label = "SEMANTIC_SIMILARITY"
                explanation = f"High semantic similarity detected between '{src_name}' and '{tgt_name}'."
            conf = round(0.70 + (h % 20) / 100.0, 2)

        out = M5SemanticEdgeLabelerOutput(
            semantic_label=label,
            confidence=conf,
            explanation=explanation,
        )
        return label, conf, explanation, out


class MockModelPipeline:
    """Unified pipeline wrapping deterministic mock implementations of M1-M5."""

    def __init__(self):
        self.m1 = MockM1Summarizer()
        self.m2 = MockM2DocScorer()
        self.m3 = MockM3IntentClassifier()
        self.m4 = MockM4SmellDetector()
        self.m5 = MockM5EdgeLabeler()

    def analyze_function(
        self, code: str, docstring: Optional[str] = None
    ) -> Dict[str, BaseModel]:
        """Runs M1-M4 on a function code snippet."""
        return {
            "summary": self.m1.predict(code),
            "doc_score": self.m2.predict(code, docstring),
            "intents": self.m3.predict(code),
            "smells": self.m4.predict(code),
        }

    def analyze_edge(
        self,
        source_code: str,
        target_code: str,
        source_summary: Optional[str] = None,
        target_summary: Optional[str] = None,
    ) -> Dict[str, M5SemanticEdgeLabelerOutput]:
        """Runs M5 edge labeler on a pair of functions."""
        return {
            "edge_label": self.m5.predict(
                source_code, target_code, source_summary, target_summary
            )
        }
