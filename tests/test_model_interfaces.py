"""
Unit tests for CIG ML Model Inference Interfaces (M1-M5) and Mock Models.
Verifies contract validation, confidence score bounds, determinism, and edge cases.
"""

import pytest
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


# Sample code fixtures
SAMPLE_FUNC_1 = """
def authenticate_user(username: str, password_hash: str) -> bool:
    \"\"\"Authenticate a user against the credentials database.\"\"\"
    if not username or not password_hash:
        return False
    user = db.query(User).filter_by(username=username).first()
    if user and user.verify_password(password_hash):
        return True
    return False
"""

SAMPLE_FUNC_2 = """
def calculate_metrics(data: list) -> dict:
    # No docstring present
    res = {}
    for item in data:
        res[item] = res.get(item, 0) + 1
    return res
"""

SYNTAX_ERROR_CODE = """
def broken_syntax(x, y:
    return x +
"""

LONG_CODE_SNIPPET = "\n".join([f"def func_{i}(): pass" for i in range(200)])


class TestM1CodeSummarizer:
    """Tests for M1 CodeT5 Summarizer and MockM1Summarizer."""

    def test_mock_m1_summarizer_basic(self):
        model = MockM1Summarizer()
        summary, output = model.summarize(SAMPLE_FUNC_1)

        assert isinstance(summary, str)
        assert len(summary) > 0
        assert isinstance(output, M1CodeSummarizerOutput)
        assert output.summary == summary
        assert 0.0 <= output.confidence <= 1.0

    def test_mock_m1_determinism(self):
        model = MockM1Summarizer()
        res1 = model.predict(SAMPLE_FUNC_1)
        res2 = model.predict(SAMPLE_FUNC_1)

        assert res1.summary == res2.summary
        assert res1.confidence == res2.confidence

    def test_mock_m1_edge_cases(self):
        model = MockM1Summarizer()

        # Empty string
        empty_out = model.predict("")
        assert isinstance(empty_out, M1CodeSummarizerOutput)
        assert 0.0 <= empty_out.confidence <= 1.0

        # Syntax error
        syntax_out = model.predict(SYNTAX_ERROR_CODE)
        assert isinstance(syntax_out, M1CodeSummarizerOutput)

        # Long code
        long_out = model.predict(LONG_CODE_SNIPPET)
        assert isinstance(long_out, M1CodeSummarizerOutput)

    def test_codet5_summarizer_interface(self):
        model = CodeT5Summarizer(use_mock_fallback=True)
        summary, output = model.summarize(SAMPLE_FUNC_1)

        assert isinstance(summary, str)
        assert isinstance(output, M1CodeSummarizerOutput)
        assert 0.0 <= output.confidence <= 1.0


class TestM2DocScorer:
    """Tests for M2 CodeBERT Doc Scorer and MockM2DocScorer."""

    def test_mock_m2_doc_scorer_with_docstring(self):
        model = MockM2DocScorer()
        docstring = "Authenticate a user against the credentials database."
        score, issues, output = model.score_docstring(SAMPLE_FUNC_1, docstring)

        assert 0.0 <= score <= 100.0
        assert isinstance(issues, list)
        assert isinstance(output, M2DocScorerOutput)
        assert 0.0 <= output.doc_quality_score <= 1.0
        assert pytest.approx(output.doc_quality_score * 100, 0.01) == score
        assert 0.0 <= output.confidence <= 1.0

    def test_mock_m2_doc_scorer_missing_docstring(self):
        model = MockM2DocScorer()
        score, issues, output = model.score_docstring(SAMPLE_FUNC_2, None)

        assert score < 50.0  # missing docstring penalty
        assert len(issues) > 0
        assert "docstring" in issues[0].lower() or "missing" in issues[0].lower()
        assert isinstance(output, M2DocScorerOutput)

    def test_mock_m2_determinism(self):
        model = MockM2DocScorer()
        res1 = model.predict(SAMPLE_FUNC_1, "Sample docstring")
        res2 = model.predict(SAMPLE_FUNC_1, "Sample docstring")

        assert res1.doc_quality_score == res2.doc_quality_score
        assert res1.doc_feedback == res2.doc_feedback
        assert res1.confidence == res2.confidence

    def test_codebert_doc_scorer_interface(self):
        model = CodeBERTDocScorer(use_mock_fallback=True)
        output = model.predict(SAMPLE_FUNC_1, "Authenticate user")

        assert isinstance(output, M2DocScorerOutput)
        assert 0.0 <= output.doc_quality_score <= 1.0


class TestM3IntentClassifier:
    """Tests for M3 CodeBERT Intent Classifier and MockM3IntentClassifier."""

    def test_mock_m3_intent_classifier_basic(self):
        model = MockM3IntentClassifier()
        labels, probs, output = model.classify(SAMPLE_FUNC_1)

        assert isinstance(labels, list)
        assert all(isinstance(lbl, IntentCategory) for lbl in labels)
        assert isinstance(probs, dict)
        assert len(probs) == len(INTENT_TAXONOMY)
        assert isinstance(output, M3IntentClassifierOutput)
        assert 0.0 <= output.confidence <= 1.0

        # SAMPLE_FUNC_1 contains authentication code
        assert IntentCategory.AUTHENTICATION in labels

    def test_mock_m3_determinism(self):
        model = MockM3IntentClassifier()
        res1 = model.predict(SAMPLE_FUNC_1)
        res2 = model.predict(SAMPLE_FUNC_1)

        assert res1.intent_labels == res2.intent_labels
        assert res1.label_probabilities == res2.label_probabilities
        assert res1.confidence == res2.confidence

    def test_mock_m3_edge_cases(self):
        model = MockM3IntentClassifier()

        empty_out = model.predict("")
        assert isinstance(empty_out, M3IntentClassifierOutput)
        assert 0.0 <= empty_out.confidence <= 1.0

        syntax_out = model.predict(SYNTAX_ERROR_CODE)
        assert isinstance(syntax_out, M3IntentClassifierOutput)

    def test_codebert_intent_classifier_interface(self):
        model = CodeBERTIntentClassifier(use_mock_fallback=True)
        labels, probs, output = model.classify(SAMPLE_FUNC_1)

        assert isinstance(output, M3IntentClassifierOutput)
        assert IntentCategory.AUTHENTICATION in labels


class TestM4SmellDetector:
    """Tests for M4 GraphCodeBERT Smell Detector and MockM4SmellDetector."""

    def test_mock_m4_smell_detector_basic(self):
        model = MockM4SmellDetector()
        probs, output = model.detect_smells(SAMPLE_FUNC_1)

        assert isinstance(probs, dict)
        assert len(probs) == len(SMELL_TAXONOMY)
        assert isinstance(output, M4SmellDetectorOutput)
        assert all(0.0 <= p <= 1.0 for p in probs.values())
        assert 0.0 <= output.confidence <= 1.0

    def test_mock_m4_god_function_detection(self):
        model = MockM4SmellDetector()
        god_func = "def god_func():\n" + "\n".join([f"    x_{i} = {i}" for i in range(100)])
        probs, output = model.detect_smells(god_func)

        assert SmellCategory.GOD_FUNCTION in output.smell_labels

    def test_mock_m4_determinism(self):
        model = MockM4SmellDetector()
        res1 = model.predict(SAMPLE_FUNC_1)
        res2 = model.predict(SAMPLE_FUNC_1)

        assert res1.smell_labels == res2.smell_labels
        assert res1.smell_probabilities == res2.smell_probabilities
        assert res1.confidence == res2.confidence

    def test_graphcodebert_smell_detector_interface(self):
        model = GraphCodeBERTSmellDetector(use_mock_fallback=True)
        output = model.predict(SAMPLE_FUNC_1)

        assert isinstance(output, M4SmellDetectorOutput)


class TestM5EdgeLabeler:
    """Tests for M5 DeBERTa Edge Labeler and MockM5EdgeLabeler."""

    def test_mock_m5_edge_labeler_basic(self):
        model = MockM5EdgeLabeler()
        label, conf, exp, output = model.label_edge(
            source_code=SAMPLE_FUNC_1,
            target_code=SAMPLE_FUNC_2,
            source_summary="Authenticates a user.",
            target_summary="Calculates item counts.",
        )

        assert isinstance(label, str)
        assert len(label) > 0
        assert 0.0 <= conf <= 1.0
        assert isinstance(exp, str)
        assert isinstance(output, M5SemanticEdgeLabelerOutput)
        assert output.semantic_label == label
        assert output.confidence == conf
        assert output.explanation == exp

    def test_mock_m5_determinism(self):
        model = MockM5EdgeLabeler()
        res1 = model.predict(SAMPLE_FUNC_1, SAMPLE_FUNC_2)
        res2 = model.predict(SAMPLE_FUNC_1, SAMPLE_FUNC_2)

        assert res1.semantic_label == res2.semantic_label
        assert res1.confidence == res2.confidence
        assert res1.explanation == res2.explanation

    def test_deberta_edge_labeler_interface(self):
        model = DeBERTaEdgeLabeler(use_mock_fallback=True)
        output = model.predict(SAMPLE_FUNC_1, SAMPLE_FUNC_2)

        assert isinstance(output, M5SemanticEdgeLabelerOutput)
        assert 0.0 <= output.confidence <= 1.0


class TestMockModelPipeline:
    """Tests for MockModelPipeline orchestrator."""

    def test_pipeline_analyze_function(self):
        pipeline = MockModelPipeline()
        result = pipeline.analyze_function(SAMPLE_FUNC_1, docstring="Authenticate user")

        assert "summary" in result
        assert isinstance(result["summary"], M1CodeSummarizerOutput)

        assert "doc_score" in result
        assert isinstance(result["doc_score"], M2DocScorerOutput)

        assert "intents" in result
        assert isinstance(result["intents"], M3IntentClassifierOutput)

        assert "smells" in result
        assert isinstance(result["smells"], M4SmellDetectorOutput)

    def test_pipeline_analyze_edge(self):
        pipeline = MockModelPipeline()
        result = pipeline.analyze_edge(SAMPLE_FUNC_1, SAMPLE_FUNC_2)

        assert "edge_label" in result
        assert isinstance(result["edge_label"], M5SemanticEdgeLabelerOutput)
