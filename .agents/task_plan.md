# Codebase Intelligence Graph (CIG) — Master Task Plan

Master execution plan for building the Codebase Intelligence Graph (CIG) system.

## Task Goal
Build an end-to-end Codebase Intelligence Graph system that parses repository code into typed structural AST graphs, enriches nodes and edges with 5 specialized NLP models, persists graph data in Neo4j, enables vector retrieval via FAISS, and exposes graph exploration through FastAPI endpoints and an interactive React/D3.js frontend UI.

## Current System State
- **Status**: Executing Phase 8.
- **Next Step**: Complete Phase 8 — Frontend Visualization (React, D3.js, TailwindCSS).

---

## Phase Overview & Delivery Order

| Phase | Description | Subagent Owner | Status |
| --- | --- | --- | --- |
| **Phase 1** | Graph Schema and Typed Contracts | `graph_engineer` / `api_designer` | `complete` |
| **Phase 2** | Parsing and AST Extraction | `parser_engineer` | `complete` |
| **Phase 3** | Structural Graph Construction | `graph_engineer` | `complete` |
| **Phase 4** | Persistence Layer and Cypher Access (Neo4j) | `graph_engineer` / `backend_developer` | `complete` |
| **Phase 5** | Model Inference Interfaces and Mock Outputs | `ml_engineer` | `complete` |
| **Phase 6** | RAG Indexing and Semantic Retrieval (FAISS) | `backend_developer` / `ml_engineer` | `complete` |
| **Phase 7** | API Endpoints (FastAPI, Celery, Redis) | `api_designer` / `backend_developer` | `complete` |
| **Phase 8** | Frontend Visualization (React, D3.js, TailwindCSS) | `frontend_developer` | `todo` |
| **Phase 9** | Training and Evaluation Refinement | `eval_engineer` / `ml_engineer` | `todo` |

---

## Detailed Phase Specifications

### Phase 1: Graph Schema and Typed Contracts
- **Goal**: Define robust Pydantic data models for nodes (`function`, `class`, `module`), structural edges (`calls`, `imports`, `inherits`, `instantiates`), node annotations (M1-M4 outputs), edge annotations (M5 output), and REST API payload/response contracts.
- **Inputs**: Canonical vocabulary and schema specifications in `AGENTS.md` and `.agents/AGENTS.md`.
- **Outputs**: `src/cig/schemas/` (`nodes.py`, `edges.py`, `annotations.py`, `api.py`, `jobs.py`).
- **Subagent Owner**: `graph_engineer` (collaborating with `api_designer`).
- **Applicable Skills**: `test-driven-development`, `user-context`.
- **Acceptance Criteria**:
  - Full Pydantic validation suite for node types (`function`, `class`, `module`) and edge types (`calls`, `imports`, `inherits`, `instantiates`).
  - Annotation schemas cover all taxonomies (15 intent labels, 5 smell labels, documentation quality scores, edge labels).
  - 100% unit test coverage on schema validation, JSON serialization, and deserialization.
- **Status**: `todo`

---

### Phase 2: Parsing and AST Extraction
- **Goal**: Implement Tree-sitter parsing engine supporting Python to extract AST nodes, symbol definitions, file/line/column source spans, docstrings, and lexical identifiers.
- **Inputs**: Source code files, Tree-sitter Python grammar configuration.
- **Outputs**: `src/cig/parser/` (`engine.py`, `ast_visitor.py`, `symbol_extractor.py`, `language_config.py`).
- **Subagent Owner**: `parser_engineer`.
- **Applicable Skills**: `test-driven-development`.
- **Acceptance Criteria**:
  - Tree-sitter accurately parses valid Python repositories into symbol structures.
  - Extracts exact start/end character offsets, line spans, docstrings, and function signatures.
  - Unit tests verify AST symbol extraction against reference Python source files.
- **Status**: `todo`

---

### Phase 3: Structural Graph Construction
- **Goal**: Build an in-memory graph constructor that processes extracted AST symbols to resolve cross-symbol references, constructing directed typed graphs with structural edges (`calls`, `imports`, `inherits`, `instantiates`).
- **Inputs**: Extracted AST symbols, source spans, and scope metadata from Phase 2.
- **Outputs**: `src/cig/graph/` (`builder.py`, `resolver.py`, `graph_model.py`).
- **Subagent Owner**: `graph_engineer`.
- **Applicable Skills**: `test-driven-development`.
- **Acceptance Criteria**:
  - Accurately resolves local and cross-module function calls, class inheritances, module imports, and class instantiations.
  - Handles scope nesting (e.g. methods within classes, nested functions) cleanly.
  - Graph constructor unit tests confirm valid directed edge creation across multi-file sample Python projects.
- **Status**: `todo`

---

### Phase 4: Persistence Layer and Cypher Access (Neo4j)
- **Goal**: Create Neo4j Community Edition driver and Cypher query layer to persist structural graphs, index node keys, store annotations, and perform graph traversals/impact analysis queries.
- **Inputs**: In-memory structural graphs from Phase 3, Neo4j connection configuration.
- **Outputs**: `src/cig/storage/` (`neo4j_client.py`, `cypher_queries.py`, `schema_migrations.py`).
- **Subagent Owner**: `graph_engineer` (collaborating with `backend_developer`).
- **Applicable Skills**: `test-driven-development`, `verification-before-completion`.
- **Acceptance Criteria**:
  - Neo4j schema constraints enforce node key uniqueness and typed edge properties.
  - Transactional persistence of nodes, edges, and model annotations.
  - Cypher query suite supports node detail retrieval, filtered graph queries, and impact analysis traversals in <100ms.
- **Status**: `todo`

---

### Phase 5: Model Inference Interfaces and Mock Outputs
- **Goal**: Define unified inference interfaces for the 5 specialized NLP models (M1 CodeT5, M2 CodeBERT Scorer, M3 CodeBERT Classifier, M4 GraphCodeBERT Smell Detector, M5 DeBERTa Cross-Encoder) with pluggable real & deterministic mock providers.
- **Inputs**: AST nodes, snippet code blocks, candidate model checkpoints.
- **Outputs**: `src/cig/models/` (`base.py`, `m1_summarizer.py`, `m2_doc_scorer.py`, `m3_intent.py`, `m4_smell.py`, `m5_edge_labeler.py`, `mock_providers.py`).
- **Subagent Owner**: `ml_engineer`.
- **Applicable Skills**: `test-driven-development`.
- **Acceptance Criteria**:
  - Standardized `InferencePipeline` class capable of invoking M1-M5 models individually or in batch.
  - Mock model implementations return realistic annotations with confidence scores without requiring heavy GPU weights during CI tests.
  - Batch inference pipelines handle node lists cleanly without memory leaks.
- **Status**: `todo`

---

### Phase 6: RAG Indexing and Semantic Retrieval (FAISS)
- **Goal**: Implement embedding generation and local FAISS vector search indexing to enable semantic codebase search and hybrid graph-grounded retrieval.
- **Inputs**: Node code snippets, node summaries, base embedding model (UniXcoder / CodeBERT).
- **Outputs**: `src/cig/retrieval/` (`embedder.py`, `faiss_indexer.py`, `hybrid_search.py`).
- **Subagent Owner**: `backend_developer` / `ml_engineer` (collaborating with `performance_optimizer`).
- **Applicable Skills**: `test-driven-development`, `rag-agent-builder`.
- **Acceptance Criteria**:
  - Embeddings generated for function/class nodes and indexed in FAISS.
  - Top-k vector similarity search operates with <50ms query latency.
  - Hybrid search combines FAISS semantic matches with Neo4j graph context and metadata filters.
- **Status**: `todo`

---

### Phase 7: API Endpoints (FastAPI, Celery, Redis)
- **Goal**: Build FastAPI REST API service for repository ingestion, ingestion job monitoring, node/edge exploration, semantic search, filtering, and impact analysis, backed by Celery/Redis asynchronous job workers.
- **Inputs**: Storage layer, retrieval engine, model pipeline, task queue configuration.
- **Outputs**: `src/cig/api/` (`main.py`, `routes/`, `tasks/`, `dependencies.py`).
- **Subagent Owner**: `api_designer` / `backend_developer`.
- **Applicable Skills**: `test-driven-development`, `verification-before-completion`.
- **Acceptance Criteria**:
  - FastAPI router provides endpoints: `/ingest`, `/status/{job_id}`, `/nodes/{id}`, `/graph`, `/search`, `/impact/{id}`.
  - Celery background workers process repository parsing, model enrichment, and graph persistence asynchronously.
  - Full OpenAPI documentation generated automatically; unit/integration tests verify API endpoints.
- **Status**: `todo`

---

### Phase 8: Frontend Visualization (React, D3.js, TailwindCSS)
- **Goal**: Implement an interactive, responsive web frontend dashboard using React, D3.js, and TailwindCSS for graph exploration, node inspection, search, and filtering.
- **Inputs**: FastAPI backend REST endpoints, OpenAPI schema.
- **Outputs**: `frontend/` (`src/components/GraphViewer.jsx`, `src/components/NodeDrawer.jsx`, `src/components/FilterBar.jsx`, `src/components/SearchBox.jsx`).
- **Subagent Owner**: `frontend_developer`.
- **Applicable Skills**: `verification-before-completion`.
- **Acceptance Criteria**:
  - D3.js force-directed or hierarchical graph layout rendering code structure dynamically.
  - Composable filtering by intent taxonomy, code smell, documentation score range, and file path.
  - Clicking any node opens a detail drawer displaying M1 summary, M2 doc score, M3 intent labels, M4 smells, and code evidence snippets.
- **Status**: `todo`

---

### Phase 9: Training and Evaluation Refinement
- **Goal**: Train and fine-tune base models (CodeT5, CodeBERT, GraphCodeBERT, DeBERTa) using PyTorch, HuggingFace, and PEFT/LoRA, track experiments via Weights & Biases, and evaluate metrics against target thresholds.
- **Inputs**: Training datasets, benchmark suites, W&B project configuration.
- **Outputs**: `src/cig/evals/` (`train.py`, `evaluate.py`, `metrics.py`, `wandb_logger.py`).
- **Subagent Owner**: `eval_engineer` / `ml_engineer`.
- **Applicable Skills**: `agentic-eval`, `verification-before-completion`.
- **Acceptance Criteria**:
  - M1 CodeT5 BLEU-4 target: `> 18`.
  - M2 CodeBERT doc quality Spearman correlation target: `> 0.65`.
  - M3 CodeBERT intent macro F1 target: `> 0.72`.
  - M4 GraphCodeBERT smell AUC-ROC target: `> 0.80`.
  - M5 DeBERTa edge accuracy target: `> 0.75`.
  - W&B dashboards log experiment parameters, loss curves, and evaluation metrics cleanly.
- **Status**: `todo`

---

## Key Architectural Risks & Mitigation Strategies

1. **Neo4j Community Write Locks**: Celery background workers must update Neo4j via serialized/batched transactions to avoid database lock contention.
2. **FAISS State Sync**: Maintain deterministic ID mappings between Neo4j node IDs and FAISS vector indices to ensure search consistency.
3. **Inference Performance**: Use lightweight mock providers for rapid local testing and development; utilize PyTorch batching/quantization for production inference.
4. **D3 Rendering Scalability**: Implement visual node aggregation and bounding viewport filters for codebases with >1,000 nodes.
