"""
Unit tests for CIG graph schema, nodes, edges, contracts, and taxonomies.
"""

import pytest
from pydantic import ValidationError

from cig.graph_schema.contracts import (
    M1CodeSummarizerOutput,
    M2DocScorerOutput,
    M3IntentClassifierOutput,
    M4SmellDetectorOutput,
    M5SemanticEdgeLabelerOutput,
    INTENT_TAXONOMY,
    SMELL_TAXONOMY,
    IntentCategory,
    SmellCategory,
)
from cig.graph_schema.nodes import (
    SourceSpan,
    NodeAnnotations,
    FunctionNode,
    ClassNode,
    ModuleNode,
    NodeType,
)
from cig.graph_schema.edges import (
    SemanticEdgeAnnotation,
    StructuralEdge,
    CallsEdge,
    ImportsEdge,
    InheritsEdge,
    InstantiatesEdge,
    StructuralEdgeType,
)


# ============================================================================
# Taxonomy & Enum Tests
# ============================================================================

def test_intent_taxonomy_count_and_values():
    """Verify that intent taxonomy contains exactly 15 valid categories."""
    assert len(INTENT_TAXONOMY) == 15
    expected_intents = {
        "authentication",
        "data processing",
        "API communication",
        "business logic",
        "database",
        "UI rendering",
        "testing",
        "configuration",
        "error handling",
        "caching",
        "logging",
        "file I/O",
        "machine learning",
        "messaging",
        "utility",
    }
    assert set(INTENT_TAXONOMY) == expected_intents
    assert set(e.value for e in IntentCategory) == expected_intents


def test_smell_taxonomy_count_and_values():
    """Verify that smell taxonomy contains exactly 5 valid categories."""
    assert len(SMELL_TAXONOMY) == 5
    expected_smells = {
        "god function",
        "misleading name",
        "dead code",
        "naming inconsistency",
        "comment-code mismatch",
    }
    assert set(SMELL_TAXONOMY) == expected_smells
    assert set(e.value for e in SmellCategory) == expected_smells


def test_node_types_enum():
    """Verify node types enum values."""
    assert set(e.value for e in NodeType) == {"function", "class", "module"}


def test_structural_edge_types_enum():
    """Verify structural edge types enum values."""
    assert set(e.value for e in StructuralEdgeType) == {
        "calls",
        "imports",
        "inherits",
        "instantiates",
    }


# ============================================================================
# Model Output Payload Contracts Tests (M1 - M5)
# ============================================================================

def test_m1_contract_valid():
    """Test valid M1 CodeT5 Summarizer contract."""
    m1 = M1CodeSummarizerOutput(summary="Calculates the sum of two integers.", confidence=0.92)
    assert m1.summary == "Calculates the sum of two integers."
    assert m1.confidence == 0.92


def test_m1_contract_invalid_confidence():
    """Test M1 contract rejects invalid confidence scores (<0 or >1)."""
    with pytest.raises(ValidationError):
        M1CodeSummarizerOutput(summary="Test", confidence=1.5)
    with pytest.raises(ValidationError):
        M1CodeSummarizerOutput(summary="Test", confidence=-0.1)


def test_m2_contract_valid():
    """Test valid M2 CodeBERT Doc Scorer contract."""
    m2 = M2DocScorerOutput(
        doc_quality_score=0.85,
        doc_feedback="Clear parameter descriptions, missing return type annotation.",
        confidence=0.88,
    )
    assert m2.doc_quality_score == 0.85
    assert m2.doc_feedback == "Clear parameter descriptions, missing return type annotation."
    assert m2.confidence == 0.88


def test_m2_contract_invalid_doc_score():
    """Test M2 contract rejects invalid doc quality score (<0 or >1)."""
    with pytest.raises(ValidationError):
        M2DocScorerOutput(doc_quality_score=1.2, doc_feedback="Invalid", confidence=0.5)


def test_m3_contract_valid():
    """Test valid M3 CodeBERT Intent Classifier contract."""
    m3 = M3IntentClassifierOutput(
        intent_labels=["authentication", "database"],
        label_probabilities={"authentication": 0.95, "database": 0.80},
        confidence=0.90,
    )
    assert m3.intent_labels == ["authentication", "database"]
    assert m3.confidence == 0.90



def test_m3_contract_strict_taxonomy():
    """Test valid M3 contract with taxonomy intent labels."""
    m3 = M3IntentClassifierOutput(
        intent_labels=["authentication", "database"],
        label_probabilities={"authentication": 0.91, "database": 0.74},
        confidence=0.89,
    )
    assert m3.intent_labels == ["authentication", "database"]
    assert m3.label_probabilities["authentication"] == 0.91
    assert m3.confidence == 0.89


def test_m3_contract_invalid_label():
    """Test M3 contract rejects labels outside Intent Taxonomy."""
    with pytest.raises(ValidationError):
        M3IntentClassifierOutput(
            intent_labels=["invalid_intent"],
            confidence=0.8,
        )


def test_m4_contract_valid():
    """Test valid M4 GraphCodeBERT Smell Detector contract."""
    m4 = M4SmellDetectorOutput(
        smell_labels=["god function", "dead code"],
        smell_probabilities={"god function": 0.82, "dead code": 0.65},
        confidence=0.84,
    )
    assert m4.smell_labels == ["god function", "dead code"]
    assert m4.confidence == 0.84


def test_m4_contract_invalid_label():
    """Test M4 contract rejects labels outside Smell Taxonomy."""
    with pytest.raises(ValidationError):
        M4SmellDetectorOutput(
            smell_labels=["spaghetti code"],
            confidence=0.8,
        )


def test_m5_contract_valid():
    """Test valid M5 DeBERTa Semantic Edge Labeler contract."""
    m5 = M5SemanticEdgeLabelerOutput(
        semantic_label="authenticates_user_credentials",
        confidence=0.95,
        explanation="Function authenticates tokens before delegating request processing.",
    )
    assert m5.semantic_label == "authenticates_user_credentials"
    assert m5.confidence == 0.95
    assert m5.explanation.startswith("Function authenticates")


def test_m5_contract_invalid_confidence():
    """Test M5 contract rejects invalid confidence scores."""
    with pytest.raises(ValidationError):
        M5SemanticEdgeLabelerOutput(
            semantic_label="label",
            confidence=2.0,
            explanation="explanation",
        )


# ============================================================================
# Node Models Tests
# ============================================================================

def test_source_span_valid():
    """Test valid source span model."""
    span = SourceSpan(start_line=10, start_column=4, end_line=25, end_column=20)
    assert span.start_line == 10
    assert span.start_column == 4
    assert span.end_line == 25
    assert span.end_column == 20


def test_source_span_invalid():
    """Test source span validates non-negative bounds."""
    with pytest.raises(ValidationError):
        SourceSpan(start_line=0, start_column=0, end_line=10, end_column=5)


def test_function_node_creation():
    """Test FunctionNode creation with structural facts and annotations."""
    span = SourceSpan(start_line=1, start_column=0, end_line=15, end_column=20)
    node = FunctionNode(
        id="mod.py::auth_user",
        name="auth_user",
        file_path="src/mod.py",
        source_span=span,
        signature="def auth_user(token: str) -> bool",
        parameters=["token"],
        return_type="bool",
        is_async=True,
    )
    assert node.node_type == NodeType.FUNCTION
    assert node.id == "mod.py::auth_user"
    assert node.name == "auth_user"
    assert node.is_async is True
    assert node.annotations.summary is None


def test_class_node_creation():
    """Test ClassNode creation."""
    span = SourceSpan(start_line=20, start_column=0, end_line=60, end_column=12)
    node = ClassNode(
        id="mod.py::AuthService",
        name="AuthService",
        file_path="src/mod.py",
        source_span=span,
        base_classes=["BaseService"],
        methods=["login", "logout"],
    )
    assert node.node_type == NodeType.CLASS
    assert node.id == "mod.py::AuthService"
    assert "BaseService" in node.base_classes
    assert "login" in node.methods


def test_module_node_creation():
    """Test ModuleNode creation."""
    span = SourceSpan(start_line=1, start_column=0, end_line=100, end_column=0)
    node = ModuleNode(
        id="src/mod.py",
        name="mod",
        file_path="src/mod.py",
        source_span=span,
        module_path="src.mod",
        imported_modules=["os", "sys", "pydantic"],
    )
    assert node.node_type == NodeType.MODULE
    assert node.module_path == "src.mod"
    assert "pydantic" in node.imported_modules


def test_node_annotations_integration():
    """Test applying model outputs (M1-M4) to node annotations while keeping structural facts separate."""
    span = SourceSpan(start_line=1, start_column=0, end_line=10, end_column=5)
    node = FunctionNode(
        id="func_1",
        name="process_data",
        file_path="src/data.py",
        source_span=span,
    )

    # Attach M1 output
    m1 = M1CodeSummarizerOutput(summary="Processes incoming data batch.", confidence=0.90)
    node.annotations.apply_m1(m1)

    # Attach M2 output
    m2 = M2DocScorerOutput(doc_quality_score=0.9, doc_feedback="Excellent docstring.", confidence=0.85)
    node.annotations.apply_m2(m2)

    # Attach M3 output
    m3 = M3IntentClassifierOutput(
        intent_labels=["data processing", "utility"],
        label_probabilities={"data processing": 0.95, "utility": 0.60},
        confidence=0.92,
    )
    node.annotations.apply_m3(m3)

    # Attach M4 output
    m4 = M4SmellDetectorOutput(
        smell_labels=["god function"],
        smell_probabilities={"god function": 0.81},
        confidence=0.83,
    )
    node.annotations.apply_m4(m4)

    # Verify structural facts remained unchanged
    assert node.id == "func_1"
    assert node.name == "process_data"

    # Verify annotations match attached model outputs
    assert node.annotations.summary == "Processes incoming data batch."
    assert node.annotations.doc_quality_score == 0.9
    assert node.annotations.doc_feedback == "Excellent docstring."
    assert node.annotations.intent_labels == ["data processing", "utility"]
    assert node.annotations.smell_labels == ["god function"]
    assert node.annotations.smell_probabilities == {"god function": 0.81}

    # Test top-level node properties for convenience
    assert node.summary == "Processes incoming data batch."
    assert node.doc_quality_score == 0.9
    assert node.doc_feedback == "Excellent docstring."
    assert node.intent_labels == ["data processing", "utility"]
    assert node.smell_labels == ["god function"]
    assert node.smell_probabilities == {"god function": 0.81}


def test_node_json_serialization():
    """Test node JSON roundtrip serialization and deserialization."""
    span = SourceSpan(start_line=1, start_column=0, end_line=5, end_column=10)
    node = FunctionNode(
        id="func_test",
        name="test_func",
        file_path="test.py",
        source_span=span,
    )
    m1 = M1CodeSummarizerOutput(summary="Test function summary.", confidence=0.9)
    node.annotations.apply_m1(m1)

    json_str = node.model_dump_json()
    deserialized = FunctionNode.model_validate_json(json_str)

    assert deserialized.id == node.id
    assert deserialized.annotations.summary == "Test function summary."


# ============================================================================
# Edge Models Tests
# ============================================================================

def test_structural_edges_creation():
    """Test creation of structural edges: calls, imports, inherits, instantiates."""
    calls = CallsEdge(id="edge_1", source_id="func_a", target_id="func_b")
    assert calls.edge_type == StructuralEdgeType.CALLS
    assert calls.source_id == "func_a"
    assert calls.target_id == "func_b"

    imports = ImportsEdge(id="edge_2", source_id="mod_a", target_id="mod_b")
    assert imports.edge_type == StructuralEdgeType.IMPORTS

    inherits = InheritsEdge(id="edge_3", source_id="class_child", target_id="class_parent")
    assert inherits.edge_type == StructuralEdgeType.INHERITS

    instantiates = InstantiatesEdge(id="edge_4", source_id="func_factory", target_id="class_target")
    assert instantiates.edge_type == StructuralEdgeType.INSTANTIATES


def test_edge_annotations_integration():
    """Test attaching semantic edge annotation (M5 payload) to structural edges."""
    edge = CallsEdge(id="edge_calls_1", source_id="login_route", target_id="verify_token")

    m5 = M5SemanticEdgeLabelerOutput(
        semantic_label="authenticates_request",
        confidence=0.96,
        explanation="login_route calls verify_token to validate JWT signatures.",
    )
    edge.annotations = SemanticEdgeAnnotation(
        label=m5.semantic_label,
        confidence=m5.confidence,
        explanation=m5.explanation,
    )

    assert edge.annotations.label == "authenticates_request"
    assert edge.annotations.confidence == 0.96
    assert edge.annotations.explanation.startswith("login_route calls")


def test_edge_invalid_confidence():
    """Test SemanticEdgeAnnotation rejects out-of-bound confidence."""
    with pytest.raises(ValidationError):
        SemanticEdgeAnnotation(label="calls", confidence=1.5, explanation="invalid")
