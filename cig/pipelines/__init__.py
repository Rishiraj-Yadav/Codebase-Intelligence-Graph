"""
CIG Pipelines Package: Ingestion Pipeline and Celery Async Task Execution.
"""

from cig.pipelines.celery_tasks import celery_app, get_task_status, ingest_repository_task
from cig.pipelines.ingestion_pipeline import IngestionPipeline

__all__ = [
    "IngestionPipeline",
    "celery_app",
    "ingest_repository_task",
    "get_task_status",
]
