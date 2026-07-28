"""
Schema initialization for Neo4j graph storage.
Creates constraints (e.g. unique constraint on Node id) and indexes on database startup.
"""

import logging
from typing import Any
from cig.storage.queries import SCHEMA_STATEMENTS

logger = logging.getLogger(__name__)


def initialize_schema(adapter: Any, database: str = "neo4j") -> None:
    """
    Executes constraint and index statements to prepare Neo4j schema.
    
    Args:
        adapter: Neo4jAdapter instance or driver.
        database: Neo4j database name (default: "neo4j").
    """
    if hasattr(adapter, "in_fallback_mode") and adapter.in_fallback_mode:
        logger.info("Adapter in fallback mode: skipping live Neo4j schema initialization.")
        return

    for statement in SCHEMA_STATEMENTS:
        try:
            if hasattr(adapter, "execute_query"):
                adapter.execute_query(statement, database=database)
            elif hasattr(adapter, "session"):
                with adapter.session(database=database) as session:
                    session.run(statement)
        except Exception as e:
            logger.warning(f"Error initializing schema statement '{statement[:40]}...': {e}")
