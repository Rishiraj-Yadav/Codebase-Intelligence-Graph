"""
Ingestion Pipeline orchestrating repository parsing, NLP model enrichment, Neo4j persistence, and FAISS indexing.
"""

import logging
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from cig.graph_schema.edges import SemanticEdgeAnnotation
from cig.models.mock_models import MockModelPipeline
from cig.parser import parse_repository
from cig.parser.models import ParsedRepository
from cig.retrieval.embedder import NodeEmbedder
from cig.retrieval.faiss_index import FAISSIndex
from cig.storage.neo4j_adapter import Neo4jAdapter

logger = logging.getLogger(__name__)


class IngestionPipeline:
    """
    Orchestrates the full codebase ingestion pipeline:
    1. Parse repository into AST nodes and structural edges.
    2. Enrich nodes and edges using M1-M5 NLP models.
    3. Persist enriched graph nodes and edges into Neo4j storage.
    4. Generate dense node vector embeddings and index into FAISS index.
    5. Return execution summary metadata dict.
    """

    def __init__(
        self,
        repo_path: Union[str, Path],
        neo4j_adapter: Optional[Neo4jAdapter] = None,
        model_pipeline: Optional[Any] = None,
        node_embedder: Optional[NodeEmbedder] = None,
        faiss_index: Optional[FAISSIndex] = None,
        ignore_patterns: Optional[List[str]] = None,
    ) -> None:
        self.repo_path = Path(repo_path).resolve()
        self.ignore_patterns = ignore_patterns
        self.neo4j_adapter = neo4j_adapter if neo4j_adapter is not None else Neo4jAdapter()
        self.model_pipeline = model_pipeline if model_pipeline is not None else MockModelPipeline()
        self.node_embedder = node_embedder if node_embedder is not None else NodeEmbedder(use_mock_fallback=True)
        self.faiss_index = faiss_index if faiss_index is not None else FAISSIndex()

    def run(self, faiss_index_path: Optional[str] = None) -> Dict[str, Any]:
        """
        Executes the end-to-end ingestion pipeline.

        Args:
            faiss_index_path: Optional file path to save the FAISS vector index binary and metadata.

        Returns:
            Dict[str, Any]: Execution summary dict containing repo_path, nodes_count, edges_count,
                            vector_index_size, and status.
        """
        logger.info(f"Starting ingestion pipeline for repository: {self.repo_path}")

        # 1. Parse repository
        parsed_repo: ParsedRepository = parse_repository(
            repo_path=self.repo_path,
            ignore_patterns=self.ignore_patterns,
        )

        # Build file content lookup table
        file_map = {f.file_path: f.content for f in parsed_repo.files}

        # 2. Enrich node annotations (M1-M4)
        node_code_map: Dict[str, str] = {}
        for node in parsed_repo.nodes:
            file_content = file_map.get(node.file_path, "")
            if file_content:
                lines = file_content.splitlines()
                start = max(0, node.source_span.start_line - 1)
                end = min(len(lines), node.source_span.end_line)
                node_code = "\n".join(lines[start:end])
            else:
                node_code = f"# {node.node_type} {node.name}\n"
            node_code_map[node.id] = node_code

            try:
                if hasattr(self.model_pipeline, "analyze_function"):
                    m_outputs = self.model_pipeline.analyze_function(
                        code=node_code,
                        docstring=node.docstring,
                    )
                    if "summary" in m_outputs and m_outputs["summary"]:
                        node.annotations.apply_m1(m_outputs["summary"])
                    if "doc_score" in m_outputs and m_outputs["doc_score"]:
                        node.annotations.apply_m2(m_outputs["doc_score"])
                    if "intents" in m_outputs and m_outputs["intents"]:
                        node.annotations.apply_m3(m_outputs["intents"])
                    if "smells" in m_outputs and m_outputs["smells"]:
                        node.annotations.apply_m4(m_outputs["smells"])
            except Exception as exc:
                logger.warning(f"Error enriching node {node.id}: {exc}")

        # Enrich edge annotations (M5)
        node_map = {n.id: n for n in parsed_repo.nodes}
        for edge in parsed_repo.edges:
            try:
                src_code = node_code_map.get(edge.source_id, "")
                tgt_code = node_code_map.get(edge.target_id, "")
                src_node = node_map.get(edge.source_id)
                tgt_node = node_map.get(edge.target_id)
                src_summary = src_node.summary if src_node else None
                tgt_summary = tgt_node.summary if tgt_node else None

                if hasattr(self.model_pipeline, "analyze_edge"):
                    m5_outputs = self.model_pipeline.analyze_edge(
                        source_code=src_code,
                        target_code=tgt_code,
                        source_summary=src_summary,
                        target_summary=tgt_summary,
                    )
                    m5_res = m5_outputs.get("edge_label") if isinstance(m5_outputs, dict) else m5_outputs
                    if m5_res:
                        edge.annotations = SemanticEdgeAnnotation(
                            label=m5_res.semantic_label,
                            confidence=m5_res.confidence,
                            explanation=m5_res.explanation,
                        )
            except Exception as exc:
                logger.warning(f"Error enriching edge {edge.id}: {exc}")

        # 3. Persist enriched graph into Neo4j
        self.neo4j_adapter.persist_repository(parsed_repo)

        # 4. Generate dense embeddings and index into FAISS
        node_ids = []
        vectors = []
        for node in parsed_repo.nodes:
            vec = self.node_embedder.embed_node(node)
            node_ids.append(node.id)
            vectors.append(vec)

        if node_ids and vectors:
            self.faiss_index.add_vectors(node_ids, vectors)

        if faiss_index_path:
            self.faiss_index.save(faiss_index_path)

        # 5. Execution Summary
        summary = {
            "repo_path": str(self.repo_path),
            "nodes_count": len(parsed_repo.nodes),
            "edges_count": len(parsed_repo.edges),
            "vector_index_size": len(self.faiss_index),
            "status": "COMPLETED",
        }

        logger.info(f"Ingestion pipeline completed successfully for {self.repo_path}: {summary}")
        return summary

    def ingest(self, faiss_index_path: Optional[str] = None) -> Dict[str, Any]:
        """Alias for run method."""
        return self.run(faiss_index_path=faiss_index_path)
