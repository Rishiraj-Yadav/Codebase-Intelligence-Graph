"""
Main FastAPI application entrypoint for Codebase Intelligence Graph (CIG).
"""

import logging
from contextlib import asynccontextmanager
from typing import AsyncGenerator, Dict, Any

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from cig.api.routes import graph, ingestion, search

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """
    FastAPI lifespan context manager for startup and shutdown events.
    """
    logger.info("Initializing Codebase Intelligence Graph (CIG) API service...")
    yield
    logger.info("Shutting down Codebase Intelligence Graph (CIG) API service.")


app = FastAPI(
    title="Codebase Intelligence Graph (CIG) API",
    description="REST API for asynchronous codebase ingestion, graph exploration, impact analysis, and semantic code search.",
    version="0.1.0",
    lifespan=lifespan,
)

# CORS middleware enabling unrestricted frontend exploration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Router Inclusions
app.include_router(ingestion.router)
app.include_router(graph.router)
app.include_router(search.router)


@app.get("/", summary="Root API Health Check")
def health_check() -> Dict[str, Any]:
    """
    Health check endpoint returning system status.
    """
    return {
        "status": "ok",
        "service": "Codebase Intelligence Graph API",
        "version": "0.1.0",
    }
