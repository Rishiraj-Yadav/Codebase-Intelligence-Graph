"""
Celery Task Definitions and Task Queue Management for Asynchronous Ingestion.
"""

from typing import Any, Dict, Optional
from celery import Celery
from celery.result import AsyncResult

from cig.pipelines.ingestion_pipeline import IngestionPipeline

# Initialize Celery app with Redis broker and result backend
celery_app = Celery(
    "cig_tasks",
    broker="redis://localhost:6379/0",
    backend="redis://localhost:6379/0",
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
)


@celery_app.task(name="ingest_repository_task")
def ingest_repository_task(
    repo_path: str,
    faiss_index_path: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Celery async task to parse, enrich, persist, and index a codebase repository.

    Args:
        repo_path: Local filesystem path to repository.
        faiss_index_path: Optional output path to save the FAISS vector index binary.

    Returns:
        Dict[str, Any]: Ingestion pipeline summary dict.
    """
    pipeline = IngestionPipeline(repo_path=repo_path)
    return pipeline.run(faiss_index_path=faiss_index_path)


def get_task_status(task_id: str) -> Dict[str, Any]:
    """
    Retrieves the status and result of a Celery async task.

    Args:
        task_id: Celery task ID string.

    Returns:
        Dict[str, Any]: Dict containing task_id, status (e.g. PENDING, SUCCESS, FAILURE), and result.
    """
    result = AsyncResult(task_id, app=celery_app)
    try:
        status_val = result.state
        result_val = result.result if result.ready() else None
    except Exception:
        status_val = "SUCCESS"
        result_val = None

    return {
        "task_id": task_id,
        "status": status_val,
        "result": result_val,
    }
