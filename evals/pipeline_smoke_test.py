"""
End-to-End Pipeline Smoke Test Harness.
Ingests a repository, verifies graph nodes and edges are populated in Neo4j/FAISS,
and asserts all five M1-M5 annotations (summary, doc_quality_score, intent_labels, smell_labels, semantic_label)
are present on graph entities.
"""

import os
import logging
import tempfile
from pathlib import Path
from typing import Any, Dict, Optional, Union

from cig.pipelines.ingestion_pipeline import IngestionPipeline
from cig.retrieval.embedder import NodeEmbedder
from cig.retrieval.faiss_index import FAISSIndex
from cig.storage.neo4j_adapter import Neo4jAdapter

logger = logging.getLogger(__name__)


def create_smoke_test_repository(base_dir: Path) -> Path:
    """Creates a temporary sample Python repository for smoke testing."""
    pkg = base_dir / "sample_app"
    pkg.mkdir(parents=True, exist_ok=True)

    init_file = pkg / "__init__.py"
    init_file.write_text('"""Sample app init package."""\n', encoding="utf-8")

    auth_file = pkg / "auth.py"
    auth_file.write_text(
        '"""User authentication module."""\n'
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
        '        """Create a new session token for user."""\n'
        '        token = f"token_{user_id}"\n'
        '        self.sessions[user_id] = token\n'
        '        return token\n',
        encoding="utf-8",
    )

    db_file = pkg / "database.py"
    db_file.write_text(
        '"""Database connection module."""\n'
        'from sample_app.auth import login_user\n\n'
        'def execute_query(query_str: str) -> list:\n'
        '    """Execute SQL query against database session."""\n'
        '    user_ok = login_user("admin", "secret")\n'
        '    if not user_ok:\n'
        '        raise PermissionError("Unauthorized")\n'
        '    return ["row1", "row2"]\n',
        encoding="utf-8",
    )

    return base_dir


def run_pipeline_smoke_test(
    repo_path: Optional[Union[str, Path]] = None,
    faiss_index_path: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Executes end-to-end pipeline smoke test:
    1. Instantiates IngestionPipeline with Neo4jAdapter fallback and FAISS index.
    2. Parses repository, enriches nodes/edges with M1-M5 models.
    3. Verifies Neo4j nodes and edges populated.
    4. Verifies FAISS vector index size.
    5. Asserts presence of all 5 M1-M5 annotations.

    Returns:
        Dict[str, Any]: Detailed smoke test execution summary and verification status.
    """
    temp_dir_obj = None
    if repo_path is None:
        temp_dir_obj = tempfile.TemporaryDirectory()
        repo_dir = create_smoke_test_repository(Path(temp_dir_obj.name))
    else:
        repo_dir = Path(repo_path)

    try:
        neo4j_adapter = Neo4jAdapter(fallback_mode=True)
        embedder = NodeEmbedder(use_mock_fallback=True, embedding_dim=768)
        faiss_index = FAISSIndex(dim=768)

        pipeline = IngestionPipeline(
            repo_path=repo_dir,
            neo4j_adapter=neo4j_adapter,
            node_embedder=embedder,
            faiss_index=faiss_index,
        )

        pipeline_summary = pipeline.run(faiss_index_path=faiss_index_path)

        nodes = neo4j_adapter.list_nodes_by_type()
        edges = neo4j_adapter.list_edges_by_type()

        if not nodes:
            raise AssertionError("Pipeline smoke test failed: Zero nodes persisted in Neo4j adapter.")
        if not edges:
            raise AssertionError("Pipeline smoke test failed: Zero edges persisted in Neo4j adapter.")
        if len(faiss_index) != len(nodes):
            raise AssertionError(
                f"FAISS index size mismatch: expected {len(nodes)}, got {len(faiss_index)}"
            )

        # Verify presence of all five M1-M5 model annotations
        m1_found = any(node.get("summary") and str(node.get("summary")).strip() != "" for node in nodes)
        m2_found = any(node.get("doc_quality_score", 0.0) > 0.0 for node in nodes)
        m3_found = any(isinstance(node.get("intent_labels"), list) and len(node.get("intent_labels", [])) > 0 for node in nodes)
        m4_found = any(isinstance(node.get("smell_labels"), list) for node in nodes)
        m5_found = any(edge.get("semantic_label") and str(edge.get("semantic_label")).strip() != "" for edge in edges)

        verified_annotations = {
            "m1_summary": m1_found,
            "m2_doc_quality_score": m2_found,
            "m3_intent_labels": m3_found,
            "m4_smell_labels": m4_found,
            "m5_semantic_label": m5_found,
        }

        all_annotations_passed = all(verified_annotations.values())

        if not all_annotations_passed:
            missing = [k for k, v in verified_annotations.items() if not v]
            raise AssertionError(f"Pipeline smoke test failed missing model annotations: {missing}")

        result_summary = {
            "status": "SUCCESS",
            "repo_path": str(repo_dir.resolve()),
            "nodes_count": len(nodes),
            "edges_count": len(edges),
            "faiss_index_size": len(faiss_index),
            "verified_annotations": verified_annotations,
            "pipeline_summary": pipeline_summary,
        }

        logger.info(f"Pipeline Smoke Test Passed Successfully: {result_summary}")
        return result_summary
    finally:
        if temp_dir_obj is not None:
            try:
                temp_dir_obj.cleanup()
            except Exception:
                pass


if __name__ == "__main__":
    res = run_pipeline_smoke_test()
    print(res)
