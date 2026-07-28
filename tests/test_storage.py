"""
Unit and integration tests for Phase 3: Neo4j Persistence and Graph Queries.
Tests schema initialization, node/edge persistence, Cypher query definitions,
intent/smell filtering, impact analysis traversal, and fallback/mock mode.
"""

from typing import Any, Dict, List
import pytest

from cig.graph_schema.contracts import (
    M1CodeSummarizerOutput,
    M2DocScorerOutput,
    M3IntentClassifierOutput,
    M4SmellDetectorOutput,
)
from cig.graph_schema.edges import (
    CallsEdge,
    ImportsEdge,
    InheritsEdge,
    InstantiatesEdge,
    SemanticEdgeAnnotation,
    StructuralEdgeType,
)
from cig.graph_schema.nodes import (
    ClassNode,
    FunctionNode,
    ModuleNode,
    NodeAnnotations,
    NodeType,
    SourceSpan,
)
from cig.parser.models import ParsedRepository
from cig.storage import Neo4jAdapter, initialize_schema
from cig.storage.queries import (
    FETCH_NODE_BY_ID,
    FILTER_NODES_BY_INTENT,
    FILTER_NODES_BY_SMELL,
    LIST_EDGES_BY_TYPE,
    LIST_NODES_BY_TYPE,
    get_impact_analysis_query,
)


@pytest.fixture
def sample_parsed_repo() -> ParsedRepository:
    """Constructs a sample ParsedRepository with nodes, edges, and annotations."""
    span = SourceSpan(start_line=1, start_column=0, end_line=10, end_column=20)

    # 1. Function Node A (util)
    fn_a_anno = NodeAnnotations()
    fn_a_anno.apply_m1(M1CodeSummarizerOutput(summary="Helper calculator", confidence=0.92))
    fn_a_anno.apply_m3(M3IntentClassifierOutput(intent_labels=["utility", "business logic"], confidence=0.88))
    fn_a = FunctionNode(
        id="func:pkg.math.add",
        name="add",
        file_path="pkg/math.py",
        source_span=span,
        docstring="Adds two numbers.",
        signature="def add(a: int, b: int) -> int",
        parameters=["a", "b"],
        return_type="int",
        is_async=False,
        annotations=fn_a_anno,
    )

    # 2. Function Node B (service method)
    fn_b_anno = NodeAnnotations()
    fn_b_anno.apply_m4(
        M4SmellDetectorOutput(
            smell_labels=["dead code"],
            smell_probabilities={"dead code": 0.85},
            confidence=0.85,
        )
    )
    fn_b = FunctionNode(
        id="func:pkg.service.process",
        name="process",
        file_path="pkg/service.py",
        source_span=span,
        docstring="Processes data pipeline.",
        signature="async def process(data: dict) -> bool",
        parameters=["data"],
        return_type="bool",
        is_async=True,
        annotations=fn_b_anno,
    )

    # 3. Class Node C
    cls_c_anno = NodeAnnotations()
    cls_c_anno.apply_m2(M2DocScorerOutput(doc_quality_score=0.95, doc_feedback="Good docs", confidence=0.95))
    cls_c_anno.apply_m3(M3IntentClassifierOutput(intent_labels=["data processing"], confidence=0.90))
    cls_c_anno.apply_m4(
        M4SmellDetectorOutput(
            smell_labels=["god function"],
            smell_probabilities={"god function": 0.78},
            confidence=0.78,
        )
    )
    cls_c = ClassNode(
        id="class:pkg.models.DataProcessor",
        name="DataProcessor",
        file_path="pkg/models.py",
        source_span=span,
        docstring="DataProcessor class.",
        base_classes=["BaseProcessor"],
        methods=["func:pkg.service.process"],
        annotations=cls_c_anno,
    )

    # 4. Module Node M
    mod_m = ModuleNode(
        id="module:pkg.service",
        name="service",
        file_path="pkg/service.py",
        source_span=span,
        docstring="Service module.",
        module_path="pkg.service",
        imported_modules=["pkg.math"],
    )

    # Edges
    # Edge 1: Module M imports Module pkg.math
    edge_imports = ImportsEdge(
        id="edge:pkg.service->pkg.math",
        source_id="module:pkg.service",
        target_id="module:pkg.math",
        annotations=SemanticEdgeAnnotation(
            label="dependency",
            confidence=0.95,
            explanation="Module service imports math package.",
        ),
    )

    # Edge 2: Function process calls Function add
    edge_calls = CallsEdge(
        id="edge:process->add",
        source_id="func:pkg.service.process",
        target_id="func:pkg.math.add",
        annotations=SemanticEdgeAnnotation(
            label="invokes_helper",
            confidence=0.90,
            explanation="process calls add for computation.",
        ),
    )

    # Edge 3: Class DataProcessor inherits BaseProcessor
    edge_inherits = InheritsEdge(
        id="edge:DataProcessor->BaseProcessor",
        source_id="class:pkg.models.DataProcessor",
        target_id="class:pkg.models.BaseProcessor",
    )

    # Edge 4: Function process instantiates Class DataProcessor
    edge_instantiates = InstantiatesEdge(
        id="edge:process->DataProcessor",
        source_id="func:pkg.service.process",
        target_id="class:pkg.models.DataProcessor",
    )

    return ParsedRepository(
        repo_path="/tmp/fake_repo",
        files=[],
        nodes=[fn_a, fn_b, cls_c, mod_m],
        edges=[edge_imports, edge_calls, edge_inherits, edge_instantiates],
    )


class TestCentralizedQueries:
    def test_query_constants_and_builders(self):
        assert "MATCH (n:Node {id: $node_id})" in FETCH_NODE_BY_ID
        assert "node_type: $node_type" in LIST_NODES_BY_TYPE
        assert "r.edge_type = $edge_type" in LIST_EDGES_BY_TYPE
        assert "$intent IN n.intent_labels" in FILTER_NODES_BY_INTENT
        assert "$smell IN n.smell_labels" in FILTER_NODES_BY_SMELL

        query_3_hops = get_impact_analysis_query(max_hops=3)
        assert "[*1..3]" in query_3_hops
        assert "id: $node_id" in query_3_hops

        query_1_hop = get_impact_analysis_query(max_hops=1)
        assert "[*1..1]" in query_1_hop

        with pytest.raises(ValueError):
            get_impact_analysis_query(max_hops=0)


class TestNeo4jAdapterMockFallback:
    def test_adapter_fallback_mode(self, sample_parsed_repo: ParsedRepository):
        adapter = Neo4jAdapter(fallback_mode=True)
        assert adapter.is_connected() is False or adapter.in_fallback_mode is True

        # Initialize schema in fallback mode
        initialize_schema(adapter)

        # Persist repository in fallback mode
        count = adapter.persist_repository(sample_parsed_repo)
        assert count == 4  # 4 nodes persisted

        # Fetch node by ID
        node_a = adapter.get_node_by_id("func:pkg.math.add")
        assert node_a is not None
        assert node_a["id"] == "func:pkg.math.add"
        assert node_a["name"] == "add"
        assert node_a["node_type"] == "function"
        assert "utility" in node_a["intent_labels"]

        # List nodes by type
        functions = adapter.list_nodes_by_type(NodeType.FUNCTION)
        assert len(functions) == 2
        classes = adapter.list_nodes_by_type("class")
        assert len(classes) == 1
        assert classes[0]["id"] == "class:pkg.models.DataProcessor"

        # List edges by type
        calls_edges = adapter.list_edges_by_type(StructuralEdgeType.CALLS)
        assert len(calls_edges) == 1
        assert calls_edges[0]["source_id"] == "func:pkg.service.process"
        assert calls_edges[0]["target_id"] == "func:pkg.math.add"
        assert calls_edges[0]["edge_type"] == "calls"

        imports_edges = adapter.list_edges_by_type("imports")
        assert len(imports_edges) == 1
        assert imports_edges[0]["semantic_label"] == "dependency"

        # Filter nodes by intent
        utility_nodes = adapter.filter_nodes_by_intent("utility")
        assert len(utility_nodes) == 1
        assert utility_nodes[0]["id"] == "func:pkg.math.add"

        data_model_nodes = adapter.filter_nodes_by_intent("data processing")
        assert len(data_model_nodes) == 1

        # Filter nodes by smell
        smelly_nodes = adapter.filter_nodes_by_smell("dead code")
        assert len(smelly_nodes) == 1
        assert smelly_nodes[0]["id"] == "func:pkg.service.process"

        god_class_nodes = adapter.filter_nodes_by_smell("god function")
        assert len(god_class_nodes) == 1
        assert god_class_nodes[0]["id"] == "class:pkg.models.DataProcessor"

        # Impact analysis traversal
        # process calls add, and process instantiates DataProcessor
        downstream = adapter.get_impact_analysis("func:pkg.service.process", max_hops=2)
        downstream_ids = {n["id"] for n in downstream}
        assert "func:pkg.math.add" in downstream_ids
        assert "class:pkg.models.DataProcessor" in downstream_ids

    def test_nonexistent_node_id(self):
        adapter = Neo4jAdapter(fallback_mode=True)
        res = adapter.get_node_by_id("nonexistent_id")
        assert res is None

        impact = adapter.get_impact_analysis("nonexistent_id", max_hops=2)
        assert len(impact) == 0


class TestStructuralVsSemanticEdgeProperties:
    def test_edge_property_distinction(self, sample_parsed_repo: ParsedRepository):
        adapter = Neo4jAdapter(fallback_mode=True)
        adapter.persist_repository(sample_parsed_repo)

        all_calls = adapter.list_edges_by_type("calls")
        assert len(all_calls) == 1
        edge = all_calls[0]

        # Structural properties
        assert "id" in edge
        assert "source_id" in edge
        assert "target_id" in edge
        assert "edge_type" in edge

        # Semantic properties
        assert "semantic_label" in edge
        assert edge["semantic_label"] == "invokes_helper"
        assert "semantic_confidence" in edge
        assert edge["semantic_confidence"] == 0.90
        assert "semantic_explanation" in edge
        assert "calls add" in edge["semantic_explanation"]


class TestAdapterEdgeCasesAndMocking:
    def test_context_manager(self):
        with Neo4jAdapter(fallback_mode=True) as adapter:
            assert adapter.in_fallback_mode is True
            adapter.persist_repository(ParsedRepository(repo_path="/tmp", files=[], nodes=[], edges=[]))
            assert len(adapter._memory_nodes) == 0

    def test_impact_analysis_invalid_hops(self):
        adapter = Neo4jAdapter(fallback_mode=True)
        with pytest.raises(ValueError, match="max_hops must be at least 1"):
            adapter.get_impact_analysis("func:pkg.math.add", max_hops=0)

    def test_mock_driver_interaction(from_unittest=None):
        from unittest.mock import MagicMock

        mock_driver = MagicMock()
        mock_session = MagicMock()
        mock_driver.session.return_value.__enter__.return_value = mock_session

        # Mock result for execute_query
        mock_record = MagicMock()
        mock_record.keys.return_value = ["n"]
        mock_node_obj = MagicMock()
        mock_node_obj._properties = {"id": "func:foo", "name": "foo", "node_type": "function"}
        mock_record.__getitem__.side_effect = lambda key: mock_node_obj if key == "n" else None
        mock_session.run.return_value = [mock_record]

        adapter = Neo4jAdapter(driver=mock_driver)
        assert adapter.driver == mock_driver
        assert adapter.in_fallback_mode is False

        # Run query
        res = adapter.get_node_by_id("func:foo")
        assert res is not None
        assert res["id"] == "func:foo"
        assert res["name"] == "foo"
        mock_session.run.assert_called_once()

