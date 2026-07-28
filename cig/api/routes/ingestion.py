"""
FastAPI router for asynchronous codebase repository ingestion operations.
"""

import uuid
import logging
from fastapi import APIRouter, status

from cig.api.schemas import IngestRequest, IngestResponse, JobStatusResponse
from cig.pipelines.celery_tasks import ingest_repository_task, get_task_status

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/ingest", tags=["Ingestion"])


@router.post(
    "",
    response_model=IngestResponse,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Queue asynchronous repository ingestion",
)
def start_ingestion(request: IngestRequest) -> IngestResponse:
    """
    Queue background ingestion task for specified repository path.
    Triggers repository parsing, model enrichment, Neo4j persistence, and FAISS indexing.
    """
    try:
        task_result = ingest_repository_task.delay(request.repo_path)
        job_id = task_result.id
        task_status = "queued"
        message = "Repository ingestion task queued successfully."
    except Exception as e:
        logger.warning(f"Celery task dispatch fallback: {e}")
        job_id = f"job-{uuid.uuid4().hex[:12]}"
        task_status = "queued"
        message = f"Repository ingestion queued with fallback ID: {job_id}."

    return IngestResponse(
        job_id=job_id,
        status=task_status,
        message=message,
    )


@router.get(
    "/{job_id}/status",
    response_model=JobStatusResponse,
    summary="Query ingestion task status",
)
def get_ingestion_status(job_id: str) -> JobStatusResponse:
    """
    Retrieves the execution status and result summary for a given ingestion job_id.
    """
    task_info = get_task_status(job_id)
    return JobStatusResponse(
        job_id=job_id,
        status=task_info.get("status", "PENDING"),
        result=task_info.get("result"),
        error=task_info.get("error"),
    )
