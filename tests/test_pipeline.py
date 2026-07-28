"""
Comprehensive end-to-end pipeline test suite for Phase 5.
Covers ingestion pipeline, NLP model enrichment, Neo4j persistence,
FAISS vector indexing, Celery async tasks, and semantic codebase search retrieval.
"""

import os
import tempfile
from pathlib import Path
import pytest

from cig.storage.neo4j_adapter import Neo4jAdapter
from cig.retrieval.embedder import NodeEmbedder
from cig.retrieval.faiss_index import FAISSIndex


@pytest.fixture
def sample_repo(tmp_path: Path) -> Path:
    """Creates a temporary sample repository structure with Python files."""
    pkg = tmp_path / "app"
    pkg.mkdir()
    (pkg / "__init__.py").write_text('"""App package initialization."""\n', encoding="utf-8")

    auth = pkg / "auth.py"
    auth.write_text(
        '"""Authentication module."""\n'
        'import os\n\n'
        'def login_user(username: str, password_hash: str) -> bool:\n'
        '    """Authenticate user with username and password hash."""\n'
        '    if not username or not password_hash:\n'
        '        return False\n'
        '    return True\n\n'
        'class SessionManager:\n'
        '    """Manages active user sessions."""\n'
        '    def __init__(self):\n'
        '        self.sessions = {}\n\n'
        '    def create_session(self, user_id: str) -> str:\n'
        '        """Create a new session ID for user."""\n'
        '        token = f"token_{user_id}"\n'
        '        self.sessions[user_id] = token\n'
        '        return token\n',
        encoding="utf-8"
    )

    db = pkg / "database.py"
    db.write_text(
        '"""Database connection module."""\n'
        'from app.auth import login_user\n\n'
        'def execute_query(query_str: str) -> list:\n'
        '    """Execute SQL query against database session."""\n'
        '    user_ok = login_user("admin", "secret")\n'
        '    if not user_ok:\n'
        '        raise PermissionError("Unauthorized")\n'
        '    return ["row1", "row2"]\n',
        encoding="utf-8"
    )

    return tmp_path


class TestIngestionPipeline:
    def test_pipeline_execution_and_summary(self, sample_repo: Path):
        from cig.pipelines.ingestion_pipeline import IngestionPipeline

        neo4j_mock = Neo4jAdapter(fallback_mode=True)
        embedder = NodeEmbedder(use_mock_fallback=True, embedding_dim=768)
        faiss_idx = FAISSIndex(dim=768)

        pipeline = IngestionPipeline(
            repo_path=sample_repo,
            neo4j_adapter=neo4j_mock,
            node_embedder=embedder,
            faiss_index=faiss_idx,
        )

        with tempfile.TemporaryDirectory() as tmp_dir:
            index_path = os.path.join(tmp_dir, "test.index")
            summary = pipeline.run(faiss_index_path=index_path)

            assert isinstance(summary, dict)
            assert summary["repo_path"] == str(sample_repo.resolve())
            assert summary["nodes_count"] > 0
            assert summary["edges_count"] >= 0
            assert summary["vector_index_size"] == summary["nodes_count"]
            assert summary["status"] == "COMPLETED"
            assert os.path.exists(index_path)
            assert os.path.exists(f"{index_path}.meta.json")

    def test_pipeline_nlp_enrichment(self, sample_repo: Path):
        from cig.pipelines.ingestion_pipeline import IngestionPipeline

        neo4j_mock = Neo4jAdapter(fallback_mode=True)
        pipeline = IngestionPipeline(
            repo_path=sample_repo,
            neo4j_adapter=neo4j_mock,
        )
        pipeline.run()

        # Check node enrichment in Neo4j adapter memory store
        login_node = neo4j_mock.get_node_by_id("func:app.auth.login_user")
        assert login_node is not None
        assert login_node["summary"] != ""
        assert "summary" in login_node
        assert login_node["doc_quality_score"] > 0.0
        assert isinstance(login_node["intent_labels"], list)
        assert isinstance(login_node["smell_labels"], list)

    def test_pipeline_edge_enrichment(self, sample_repo: Path):
        from cig.pipelines.ingestion_pipeline import IngestionPipeline

        neo4j_mock = Neo4jAdapter(fallback_mode=True)
        pipeline = IngestionPipeline(
            repo_path=sample_repo,
            neo4j_adapter=neo4j_mock,
        )
        pipeline.run()

        # Verify edge extraction and M5 semantic edge annotation
        edges = neo4j_mock.list_edges_by_type("calls")
        assert len(edges) > 0
        calls_edge = edges[0]
        assert "semantic_label" in calls_edge
        assert calls_edge["semantic_label"] != ""


class TestCodebaseSearchEngine:
    def test_search_retrieval_flow(self, sample_repo: Path):
        from cig.pipelines.ingestion_pipeline import IngestionPipeline
        from cig.retrieval.search import CodebaseSearchEngine

        neo4j_mock = Neo4jAdapter(fallback_mode=True)
        embedder = NodeEmbedder(use_mock_fallback=True, embedding_dim=768)
        faiss_idx = FAISSIndex(dim=768)

        pipeline = IngestionPipeline(
            repo_path=sample_repo,
            neo4j_adapter=neo4j_mock,
            node_embedder=embedder,
            faiss_index=faiss_idx,
        )
        pipeline.run()

        engine = CodebaseSearchEngine(
            neo4j_adapter=neo4j_mock,
            node_embedder=embedder,
            faiss_index=faiss_idx,
        )

        search_res = engine.search("user authentication login", top_k=3)

        assert isinstance(search_res, dict)
        assert search_res["query"] == "user authentication login"
        assert search_res["total_results"] <= 3
        assert len(search_res["results"]) > 0

        first_match = search_res["results"][0]
        assert "node_id" in first_match
        assert "score" in first_match
        assert "node" in first_match
        assert isinstance(first_match["node"], dict)

    def test_search_engine_load_from_faiss_path(self, sample_repo: Path):
        from cig.pipelines.ingestion_pipeline import IngestionPipeline
        from cig.retrieval.search import CodebaseSearchEngine

        neo4j_mock = Neo4jAdapter(fallback_mode=True)
        embedder = NodeEmbedder(use_mock_fallback=True, embedding_dim=768)

        with tempfile.TemporaryDirectory() as tmp_dir:
            index_path = os.path.join(tmp_dir, "saved.index")
            pipeline = IngestionPipeline(
                repo_path=sample_repo,
                neo4j_adapter=neo4j_mock,
                node_embedder=embedder,
            )
            pipeline.run(faiss_index_path=index_path)

            # Initialize engine with faiss_index_path
            engine = CodebaseSearchEngine(
                neo4j_adapter=neo4j_mock,
                node_embedder=embedder,
                faiss_index_path=index_path,
            )

            res = engine.search("execute query sql database", top_k=2)
            assert res["total_results"] > 0


class TestCeleryTasks:
    def test_ingest_repository_task(self, sample_repo: Path):
        from cig.pipelines.celery_tasks import celery_app, ingest_repository_task, get_task_status

        # Enable eager execution for Celery testing without a running broker
        celery_app.conf.update(
            task_always_eager=True,
            task_eager_propagates=True,
        )

        with tempfile.TemporaryDirectory() as tmp_dir:
            faiss_path = os.path.join(tmp_dir, "celery_test.index")
            task_res = ingest_repository_task.apply(args=[str(sample_repo), faiss_path])
            result_val = task_res.get()

            assert isinstance(result_val, dict)
            assert result_val["status"] == "COMPLETED"
            assert result_val["nodes_count"] > 0
            assert os.path.exists(faiss_path)

            # Test get_task_status
            status_dict = get_task_status(task_res.id)
            assert isinstance(status_dict, dict)
            assert status_dict["task_id"] == task_res.id
            assert status_dict["status"] in ("SUCCESS", "COMPLETED")
