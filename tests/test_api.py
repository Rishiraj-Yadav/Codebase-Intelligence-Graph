"""
Unit and integration tests for FastAPI API endpoints in Codebase Intelligence Graph (CIG).
Tests coverage includes:
- Root health check GET /
- CORS middleware configuration
- Ingestion routes POST /ingest and GET /ingest/{job_id}/status
- Graph exploration routes GET /nodes, GET /nodes/{node_id:path}, GET /edges, GET /nodes/{node_id:path}/impact
- 404 handling for non-existent nodes
- Natural language search route POST /search
- Response contract validation against Pydantic schemas in cig.api.schemas
"""

import pytest
from fastapi.testclient import TestClient

from cig.api.main import app
from cig.api.dependencies import get_neo4j_adapter, get_search_engine
from cig.api.schemas import (
    IngestResponse,
    JobStatusResponse,
    NodeListResponse,
    NodeDetailResponse,
    EdgeListResponse,
    ImpactAnalysisResponse,
    SearchResponse,
)
from cig.storage.neo4j_adapter import Neo4jAdapter
from cig.retrieval.search import CodebaseSearchEngine


@pytest.fixture
def mock_adapter():
    """Provides a Neo4jAdapter in fallback/in-memory mode populated with sample graph data."""
    adapter = Neo4jAdapter(fallback_mode=True)
    # Populate memory store with sample nodes
    adapter._memory_nodes = {
        "func:module.parse_code": {
            "id": "func:module.parse_code",
            "name": "parse_code",
            "node_type": "function",
            "file_path": "module.py",
            "docstring": "Parses source code into AST.",
            "start_line": 1,
            "start_column": 0,
            "end_line": 10,
            "end_column": 20,
            "signature": "def parse_code(source: str) -> AST",
            "parameters": ["source"],
            "return_type": "AST",
            "is_async": False,
            "intent_labels": ["parsing", "ast"],
            "smell_labels": [],
        },
        "class:module.Parser": {
            "id": "class:module.Parser",
            "name": "Parser",
            "node_type": "class",
            "file_path": "module.py",
            "docstring": "Main parser class.",
            "start_line": 12,
            "start_column": 0,
            "end_line": 50,
            "end_column": 0,
            "base_classes": ["BaseParser"],
            "methods": ["parse_code"],
            "intent_labels": ["parsing"],
            "smell_labels": ["god_class"],
        },
        "func:module.helper": {
            "id": "func:module.helper",
            "name": "helper",
            "node_type": "function",
            "file_path": "module.py",
            "docstring": "Helper function.",
            "start_line": 52,
            "start_column": 0,
            "end_line": 60,
            "end_column": 0,
            "intent_labels": [],
            "smell_labels": [],
        },
    }
    # Populate memory store with sample edges
    adapter._memory_edges = {
        "edge:1": {
            "id": "edge:1",
            "source_id": "class:module.Parser",
            "target_id": "func:module.parse_code",
            "edge_type": "calls",
            "semantic_label": "internal_call",
            "semantic_confidence": 0.95,
        },
        "edge:2": {
            "id": "edge:2",
            "source_id": "func:module.parse_code",
            "target_id": "func:module.helper",
            "edge_type": "calls",
            "semantic_label": "utility_call",
            "semantic_confidence": 0.90,
        },
    }
    return adapter


@pytest.fixture
def mock_search_engine(mock_adapter):
    """Provides a CodebaseSearchEngine backed by the mock adapter."""
    return CodebaseSearchEngine(neo4j_adapter=mock_adapter)


@pytest.fixture
def client(mock_adapter, mock_search_engine):
    """FastAPI TestClient with dependency overrides for Neo4jAdapter and CodebaseSearchEngine."""
    app.dependency_overrides[get_neo4j_adapter] = lambda: mock_adapter
    app.dependency_overrides[get_search_engine] = lambda: mock_search_engine
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


class TestHealthAndCORS:
    """Tests for API health check root endpoint and CORS headers."""

    def test_health_check(self, client):
        response = client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert data.get("status") == "ok"
        assert "service" in data

    def test_cors_headers(self, client):
        response = client.options(
            "/",
            headers={
                "Origin": "http://localhost:3000",
                "Access-Control-Request-Method": "GET",
            },
        )
        assert response.status_code == 200
        assert response.headers.get("access-control-allow-origin") in ["*", "http://localhost:3000"]


class TestIngestionRoutes:
    """Tests for repository ingestion routes POST /ingest and GET /ingest/{job_id}/status."""

    def test_post_ingest(self, client):
        payload = {"repo_path": "/fake/repo/path", "ignore_patterns": ["*.pyc"]}
        response = client.post("/ingest", json=payload)
        assert response.status_code in [200, 202]
        data = response.json()
        validated = IngestResponse(**data)
        assert validated.job_id != ""
        assert validated.status in ["queued", "processing", "PENDING", "STARTED", "SUCCESS"]

    def test_get_ingest_status(self, client):
        job_id = "test-job-123"
        response = client.get(f"/ingest/{job_id}/status")
        assert response.status_code == 200
        data = response.json()
        validated = JobStatusResponse(**data)
        assert validated.job_id == job_id
        assert validated.status is not None


class TestGraphRoutes:
    """Tests for graph exploration routes GET /nodes, GET /nodes/{id}, GET /edges, GET /nodes/{id}/impact."""

    def test_list_nodes_all(self, client):
        response = client.get("/nodes")
        assert response.status_code == 200
        data = response.json()
        validated = NodeListResponse(**data)
        assert validated.total == 3
        assert len(validated.nodes) == 3

    def test_list_nodes_filtered_by_type(self, client):
        response = client.get("/nodes?node_type=function")
        assert response.status_code == 200
        data = response.json()
        validated = NodeListResponse(**data)
        assert validated.total == 2
        assert validated.node_type == "function"
        assert all(n["node_type"] == "function" for n in validated.nodes)

    def test_get_node_detail_success(self, client):
        node_id = "func:module.parse_code"
        response = client.get(f"/nodes/{node_id}")
        assert response.status_code == 200
        data = response.json()
        validated = NodeDetailResponse(**data)
        assert validated.node["id"] == node_id
        assert validated.node["name"] == "parse_code"

    def test_get_node_detail_not_found(self, client):
        node_id = "nonexistent:node:id"
        response = client.get(f"/nodes/{node_id}")
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()

    def test_list_edges_all(self, client):
        response = client.get("/edges")
        assert response.status_code == 200
        data = response.json()
        validated = EdgeListResponse(**data)
        assert validated.total == 2
        assert len(validated.edges) == 2

    def test_list_edges_filtered_by_type(self, client):
        response = client.get("/edges?edge_type=calls")
        assert response.status_code == 200
        data = response.json()
        validated = EdgeListResponse(**data)
        assert validated.total == 2
        assert validated.edge_type == "calls"

    def test_get_node_impact_analysis(self, client):
        root_id = "class:module.Parser"
        response = client.get(f"/nodes/{root_id}/impact?max_hops=2")
        assert response.status_code == 200
        data = response.json()
        validated = ImpactAnalysisResponse(**data)
        assert validated.root_node_id == root_id
        assert validated.max_hops == 2
        assert validated.total_downstream >= 1
        downstream_ids = [n["id"] for n in validated.downstream_nodes]
        assert "func:module.parse_code" in downstream_ids


class TestSearchRoutes:
    """Tests for natural language search route POST /search."""

    def test_post_search_basic(self, client):
        payload = {"query": "parse code AST", "top_k": 5}
        response = client.post("/search", json=payload)
        assert response.status_code == 200
        data = response.json()
        validated = SearchResponse(**data)
        assert validated.query == "parse code AST"
        assert isinstance(validated.results, list)

    def test_post_search_with_intent_and_smell_filters(self, client):
        payload = {
            "query": "parser class",
            "top_k": 5,
            "intent_filter": "parsing",
            "smell_filter": "god_class",
        }
        response = client.post("/search", json=payload)
        assert response.status_code == 200
        data = response.json()
        validated = SearchResponse(**data)
        assert validated.query == "parser class"
        for item in validated.results:
            node = item.node
            if "intent_labels" in node:
                assert "parsing" in node["intent_labels"]
