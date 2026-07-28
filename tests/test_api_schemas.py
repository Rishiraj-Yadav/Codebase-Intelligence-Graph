"""
Unit tests for CIG Pydantic API Schemas in cig.api.schemas.
"""

import pytest
from pydantic import ValidationError

from cig.api.schemas import (
    AnnotationOutput,
    EdgeListResponse,
    ImpactAnalysisResponse,
    IngestRequest,
    IngestResponse,
    JobStatusResponse,
    NodeDetailResponse,
    NodeListResponse,
    Provenance,
    SearchRequest,
    SearchResponse,
    SearchResultItem,
    SourceSpan,
)


class TestIngestionSchemas:
    def test_ingest_request_valid(self):
        req = IngestRequest(repo_path="/path/to/repo", ignore_patterns=["*.tmp", "build/*"])
        assert req.repo_path == "/path/to/repo"
        assert req.ignore_patterns == ["*.tmp", "build/*"]

    def test_ingest_request_optional_ignore_patterns(self):
        req = IngestRequest(repo_path="/path/to/repo")
        assert req.repo_path == "/path/to/repo"
        assert req.ignore_patterns is None

    def test_ingest_response_valid(self):
        res = IngestResponse(job_id="job-12345", status="queued", message="Ingestion task started")
        assert res.job_id == "job-12345"
        assert res.status == "queued"
        assert res.message == "Ingestion task started"

    def test_job_status_response(self):
        res = JobStatusResponse(
            job_id="job-12345",
            status="SUCCESS",
            result={"modules": 10, "functions": 50},
            error=None,
        )
        assert res.job_id == "job-12345"
        assert res.status == "SUCCESS"
        assert res.result["modules"] == 10
        assert res.error is None


class TestGraphExplorationSchemas:
    def test_node_list_response(self):
        res = NodeListResponse(
            total=1,
            node_type="function",
            nodes=[
                {
                    "id": "func_1",
                    "name": "foo",
                    "node_type": "function",
                    "file_path": "main.py",
                }
            ],
        )
        assert res.total == 1
        assert res.node_type == "function"
        assert len(res.nodes) == 1
        assert res.nodes[0]["name"] == "foo"

    def test_node_detail_response(self):
        res = NodeDetailResponse(
            node={
                "id": "class_1",
                "name": "MyClass",
                "node_type": "class",
                "file_path": "models.py",
                "annotations": {"summary": "A model class"},
            }
        )
        assert res.node["name"] == "MyClass"

    def test_edge_list_response(self):
        res = EdgeListResponse(
            total=2,
            edge_type="CALLS",
            edges=[
                {"source": "f1", "target": "f2", "edge_type": "CALLS"},
                {"source": "f2", "target": "f3", "edge_type": "CALLS"},
            ],
        )
        assert res.total == 2
        assert res.edge_type == "CALLS"
        assert len(res.edges) == 2

    def test_impact_analysis_response(self):
        res = ImpactAnalysisResponse(
            root_node_id="root_func",
            max_hops=3,
            total_downstream=2,
            downstream_nodes=[
                {"id": "dep_1", "distance": 1},
                {"id": "dep_2", "distance": 2},
            ],
        )
        assert res.root_node_id == "root_func"
        assert res.max_hops == 3
        assert res.total_downstream == 2
        assert len(res.downstream_nodes) == 2


class TestSearchSchemas:
    def test_search_request_defaults(self):
        req = SearchRequest(query="find auth handler")
        assert req.query == "find auth handler"
        assert req.top_k == 5
        assert req.intent_filter is None
        assert req.smell_filter is None

    def test_search_request_with_filters(self):
        req = SearchRequest(
            query="find database functions",
            top_k=10,
            intent_filter="database",
            smell_filter="god function",
        )
        assert req.top_k == 10
        assert req.intent_filter == "database"
        assert req.smell_filter == "god function"

    def test_search_request_validation(self):
        with pytest.raises(ValidationError):
            SearchRequest(query="")

        with pytest.raises(ValidationError):
            SearchRequest(query="test", top_k=0)

    def test_search_response(self):
        item = SearchResultItem(
            node_id="node_1",
            score=0.92,
            node={"name": "authenticate_user", "file_path": "auth.py"},
        )
        res = SearchResponse(query="auth", total_results=1, results=[item])
        assert res.query == "auth"
        assert res.total_results == 1
        assert res.results[0].node_id == "node_1"
        assert res.results[0].score == 0.92


class TestAnnotationAndProvenanceSchemas:
    def test_source_span_and_provenance(self):
        span = SourceSpan(start_line=10, start_column=4, end_line=25, end_column=12)
        prov = Provenance(file_path="src/utils.py", source_span=span)
        assert prov.file_path == "src/utils.py"
        assert prov.source_span.start_line == 10

    def test_source_span_validation(self):
        with pytest.raises(ValidationError):
            SourceSpan(start_line=0, start_column=0, end_line=5, end_column=5)

    def test_annotation_output_valid(self):
        span = SourceSpan(start_line=1, start_column=0, end_line=15, end_column=0)
        ann = AnnotationOutput(
            annotation_type="summary",
            value="Handles user authentication",
            confidence=0.88,
            file_path="auth/service.py",
            source_span=span,
            evidence="Code T5 generated summary based on docstring and AST AST parsing",
        )
        assert ann.confidence == 0.88
        assert ann.file_path == "auth/service.py"
        assert ann.evidence is not None

    def test_annotation_output_confidence_bounds(self):
        span = SourceSpan(start_line=1, start_column=0, end_line=15, end_column=0)
        with pytest.raises(ValidationError):
            AnnotationOutput(
                annotation_type="smell",
                value="god function",
                confidence=1.5,  # Out of range > 1.0
                file_path="service.py",
                source_span=span,
            )

        with pytest.raises(ValidationError):
            AnnotationOutput(
                annotation_type="smell",
                value="god function",
                confidence=-0.1,  # Out of range < 0.0
                file_path="service.py",
                source_span=span,
            )
