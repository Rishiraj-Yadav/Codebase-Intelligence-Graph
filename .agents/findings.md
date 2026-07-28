# Codebase Intelligence Graph (CIG) — Research Findings & Architecture Decisions

A persistent record of architectural research, decisions, risks, taxonomies, and technical discoveries for the CIG project.

---

## 1. Key Project Facts & Canonical Semantics

### Product Identity
CIG is a semantic code understanding system that parses code repositories into typed structural graphs, enriches nodes and edges using 5 specialized NLP models, persists the output in Neo4j, enables vector retrieval via FAISS, and presents an explainable API and React/D3.js UI.

### System Stack Overview
- **Code Parsing**: Tree-sitter (Python support first)
- **Graph Database**: Neo4j Community Edition (Cypher query interface)
- **Vector Search**: FAISS (Local dense vector index)
- **Backend API & Queue**: FastAPI, Celery, Redis
- **Frontend UI**: React, D3.js, TailwindCSS
- **ML Frameworks**: PyTorch, HuggingFace Transformers, PEFT/LoRA, Weights & Biases (W&B)
- **Deployment Targets**: Docker Compose (Local), Railway (Backend), Vercel (Frontend)

### Canonical Vocabulary & Schemas

#### Node Types
- `function`
- `class`
- `module`

#### Structural Edge Types
- `calls`
- `imports`
- `inherits`
- `instantiates`

#### NLP Model Suite & Responsibilities
- **M1 (Code Summarizer)**: CodeT5 — Generates human-readable summaries for AST nodes. Target: BLEU-4 > 18.
- **M2 (Doc Quality Scorer)**: CodeBERT Regression — Scores documentation quality and generates feedback. Target: Spearman correlation > 0.65.
- **M3 (Intent Classifier)**: CodeBERT Multi-Label — Classifies function/class semantic intent across 15 taxonomies. Target: Macro F1 > 0.72.
- **M4 (Code Smell Detector)**: GraphCodeBERT Multi-Label — Detects structural and naming code smells. Target: Per-class AUC-ROC > 0.80.
- **M5 (Semantic Edge Labeler)**: DeBERTa Cross-Encoder — Labels semantic relationships between connected nodes with confidence scores & rationale. Target: Accuracy > 0.75.

#### Taxonomies
- **Intent Taxonomy (15 classes)**: `authentication`, `data processing`, `API communication`, `business logic`, `database`, `UI rendering`, `testing`, `configuration`, `error handling`, `caching`, `logging`, `file I/O`, `machine learning`, `messaging`, `utility`.
- **Code Smell Taxonomy (5 classes)**: `god function`, `misleading name`, `dead code`, `naming inconsistency`, `comment-code mismatch`.

---

## 2. Architectural Decisions & Design Patterns

1. **Modular Domain Boundaries**: Strict separation between `parser`, `graph_schema`, `models`, `pipelines`, `retrieval`, `storage`, `api`, `frontend`, and `evals`. Model internals do not leak into storage or UI code.
2. **Schema-First Pydantic Contracts**: All node representations, edge payloads, model predictions, job statuses, and REST responses are defined via Pydantic models before implementation.
3. **Deterministic Fallbacks for Development**: Vector retrieval (FAISS) and NLP inference interfaces (M1-M5) provide mock/flat deterministic implementations to allow offline development and fast CI test execution.
4. **Explainability by Design**: Annotations store raw confidence scores, label probabilities, evidence snippets, and model provenance rather than binary or opaque outputs.

---

## 3. Architectural Risks & Ambiguities

### Risk 1: Neo4j Community Edition Concurrency & Transaction Bottlenecks
- **Context**: Neo4j Community Edition runs as a single instance and does not support multi-database clustering or parallel write transactions across separate databases.
- **Risk**: Concurrent Celery ingestion tasks attempting parallel writes to Neo4j could experience deadlocks or lock wait timeouts.
- **Mitigation**: Batch graph updates per repository/module and gate write operations behind a dedicated, single-threaded or pooled Celery persistence queue.

### Risk 2: Neo4j & FAISS Vector Index Synchronization & Stale State
- **Context**: Neo4j stores structural nodes and edge relationships, while FAISS stores dense vector embeddings in an in-memory or file index. FAISS does not natively participate in Neo4j transactions.
- **Risk**: Deletions, incremental re-ingestions, or partial job failures may cause drift between FAISS index IDs and Neo4j node IDs.
- **Mitigation**: Maintain a persistent ID mapping layer in Neo4j storing vector IDs and index versions. Re-index FAISS snapshots atomically upon pipeline job completion.

### Risk 3: NLP Inference Latency & High Compute Requirements (M1-M5 Pipeline)
- **Context**: Running 5 deep learning models (CodeT5, CodeBERT, GraphCodeBERT, DeBERTa) sequentially on thousands of AST nodes during ingestion will introduce severe processing bottlenecks.
- **Risk**: Long-running ingestion jobs timing out or consuming excessive VRAM/RAM.
- **Mitigation**: Implement batch inference inside Celery workers, support CPU/GPU execution toggles, prefer quantized or PEFT/LoRA model weights for inference, and allow mock model outputs during pipeline testing.

### Risk 4: Large Graph UI Rendering Bottleneck in D3.js
- **Context**: Tree-sitter parses every function, class, and module. Medium-to-large repositories easily exceed 5,000 nodes and 20,000 edges.
- **Risk**: WebGL/DOM rendering in D3.js may freeze or lag when attempting to render thousands of nodes simultaneously.
- **Mitigation**: Implement graph visual aggregation (collapsing modules into high-level blocks), spatial sub-graph filtering, and viewport boundary rendering in the React/D3 frontend.

### Risk 5: Multi-Language Parsing Extensibility
- **Context**: Initial implementation targets Python, but tree-sitter grammars and symbol extraction logic differ significantly between languages (e.g. JavaScript, C++, Go).
- **Risk**: Tightly coupling symbol extraction logic to Python AST patterns could require refactoring when adding language support.
- **Mitigation**: Abstract AST parsing into a language-agnostic parser interface with language-specific AST strategy modules (`PythonASTStrategy`, etc.).

---

## 4. Open Questions

1. **Incremental Ingestion**: Should CIG support Git diff-based incremental re-parsing, or focus on full repository ingestion for initial milestones? *(Recommendation: Full ingestion slice first, diff-based indexing in later iterations)*.
2. **Model Checkpoint Management**: Where will model weights be hosted for local runs (HuggingFace Hub vs local disk mount)? *(Recommendation: Support HF Hub auto-download with local caching dir)*.

---

## 5. Phase 1 Schema Decisions & Key Takeaways

1. **Isolation of Structural Facts vs Model Annotations**:
   - `BaseNode` holds AST-extracted structural facts (`id`, `name`, `node_type`, `file_path`, `source_span`, `docstring`).
   - `NodeAnnotations` holds M1-M4 predictions (`summary`, `doc_quality_score`, `doc_feedback`, `intent_labels`, `smell_labels`, `smell_probabilities`).
   - This ensures model re-runs or inference pipeline updates mutate only annotation containers without touching AST ground truth.

2. **Strict Validation for Taxonomies**:
   - `IntentCategory` Enum strictly validates all 15 intent classes (`authentication`, `data processing`, `API communication`, `business logic`, `database`, `UI rendering`, `testing`, `configuration`, `error handling`, `caching`, `logging`, `file I/O`, `machine learning`, `messaging`, `utility`).
   - `SmellCategory` Enum strictly validates all 5 smell classes (`god function`, `misleading name`, `dead code`, `naming inconsistency`, `comment-code mismatch`).
   - M3 and M4 output payload contracts validate label items against these enums, rejecting arbitrary strings.

3. **Mandatory Bounded Confidence Scores Across Contracts**:
   - All M1–M5 contract output models (`M1CodeSummarizerOutput`, `M2DocScorerOutput`, `M3IntentClassifierOutput`, `M4SmellDetectorOutput`, `M5SemanticEdgeLabelerOutput`) and `SemanticEdgeAnnotation` explicitly enforce `Field(..., ge=0.0, le=1.0)` confidence scores.

4. **Discriminated Subtype Models**:
   - Node models (`FunctionNode`, `ClassNode`, `ModuleNode`) and Edge models (`CallsEdge`, `ImportsEdge`, `InheritsEdge`, `InstantiatesEdge`) use Literal discriminators for `node_type` and `edge_type`, allowing clean Pydantic polymorphism during API serialization.

---

## 6. Phase 2 Parsing & AST Extraction Decisions & Key Takeaways

1. **Tree-sitter Language Strategy Pattern**:
   - Abstracted language handling in `ASTExtractor` through specialized language handlers (`PythonASTHandler`).
   - Adding future language support (e.g. JavaScript, Go, C++) requires adding a corresponding strategy handler without modifying core repository loader logic.

2. **Deterministic Output & Stable Node IDs**:
   - File listing in `RepoLoader` sorts relative paths lexicographically using forward slashes (`/`).
   - Node IDs follow strict deterministic conventions:
     - Modules: `module:<module_path>` (e.g., `module:mypackage.models`)
     - Classes: `class:<module_path>.<class_chain>` (e.g., `class:mypackage.models.User`)
     - Functions/Methods: `func:<module_path>.<scope_chain>.<func_name>` (e.g., `func:mypackage.models.User.compute_score`)
     - Edges: `edge:<type>:<source_id>-><target_id>` (or with line number suffix for call invocations).

3. **Source Provenance Integrity**:
   - All extracted AST nodes map character ranges and line numbers into `SourceSpan` (1-indexed start/end lines, 0-indexed columns).

4. **Resilience & Fault Recovery**:
   - Tree-sitter error nodes (`ERROR` / syntax errors) do not crash parsing. The AST traverser recovers valid subtree nodes (e.g. valid classes or functions in the same file) and logs parse errors cleanly into `ParsedRepository.parse_errors`.

---

## 7. Phase 3 Neo4j Persistence & Cypher Query Decisions & Key Takeaways

1. **Centralized Cypher Statements**:
   - All Cypher statements are kept strictly in `cig/storage/queries.py` to prevent scattered or inline Cypher logic across service or API layers.

2. **Explicit Separation of Structural vs Semantic Properties**:
   - Structural edge properties (`edge_type`, `id`, `source_id`, `target_id`) are cleanly separated from semantic edge annotations (`semantic_label`, `semantic_confidence`, `semantic_explanation`).
   - Structural node properties (`id`, `name`, `node_type`, `file_path`, `source_span`, etc.) remain separated from M1-M4 annotation fields (`summary`, `doc_quality_score`, `intent_labels`, `smell_labels`).

3. **Parameterized Impact Analysis Query**:
   - Downstream impact analysis is executed via parameterized Cypher path traversals `MATCH (start:Node {id: $node_id})-[*1..N]->(downstream:Node) RETURN DISTINCT downstream`, supporting dynamic N-hop exploration.

4. **Zero-Dependency Fallback Execution Mode**:
   - `Neo4jAdapter` includes built-in fallback mode with in-memory graph structures and Cypher pattern emulation when a live Neo4j database service is offline or unreachable during unit tests.

---

## 8. Phase 4 Model Inference Interface Decisions & Key Takeaways

1. **Strict Decoupling of Inference & Training**:
   - Inference classes (`CodeT5Summarizer`, `CodeBERTDocScorer`, `CodeBERTIntentClassifier`, `GraphCodeBERTSmellDetector`, `DeBERTaEdgeLabeler`) are kept strictly separated from model training, dataset formatting, or fine-tuning pipelines.

2. **PEFT/LoRA Compatibility & HuggingFace Loading**:
   - Models support optional `peft_adapter_path` parameters to load LoRA/PEFT weights (`PeftModel.from_pretrained(...)`) on top of base pretrained checkpoints.

3. **Mandatory Bounded Confidence Scores Across Outputs**:
   - Every inference output returns typed Pydantic output contracts (`M1CodeSummarizerOutput` .. `M5SemanticEdgeLabelerOutput`) enforcing `confidence` scores bounded strictly in `[0.0, 1.0]`.

4. **Deterministic Fast Mock Implementations**:
   - `cig/models/mock_models.py` provides zero-dependency, deterministic mock providers for M1-M5 and a unified `MockModelPipeline` that produce deterministic outputs based on SHA-256 code content hashes.

---

## 9. Phase 5 Pipeline Orchestration & Retrieval Indexing Decisions & Key Takeaways

1. **End-to-End Pipeline Composition**:
   - `IngestionPipeline` sequentially links parsing (`parse_repository`), M1-M4 node enrichment, M5 edge enrichment, graph persistence (`Neo4jAdapter`), dense embedding (`NodeEmbedder`), and vector index building (`FAISSIndex`).

2. **L2-Normalized Inner Product Vector Indexing**:
   - `FAISSIndex` utilizes `faiss.IndexFlatIP` combined with L2-normalized float32 embeddings (`NodeEmbedder`), ensuring cosine similarity search without expensive distance conversions.
   - Maintains a JSON-serialized metadata sidecar (`.meta.json`) for integer index $\leftrightarrow$ string `node_id` mappings.

3. **Hybrid RAG Codebase Search Engine**:
   - `CodebaseSearchEngine` integrates vector retrieval (`FAISSIndex`) with graph storage property lookup (`Neo4jAdapter`). Queries are embedded into the same dense vector space, matched via FAISS top-k search, and hydrated with full graph annotations from Neo4j.

4. **Asynchronous Processing via Celery & Redis**:
   - Celery tasks (`ingest_repository_task`) wrap the ingestion pipeline for non-blocking asynchronous repository processing, using Redis as the broker and result backend.

---

## 10. Phase 6 API Endpoint Decisions & Key Takeaways

1. **Strict Separation of Async Ingestion & Read Query APIs**:
   - Repository ingestion (`POST /ingest`) returns an immediate asynchronous job handle (`job_id`) and status endpoint (`GET /ingest/{job_id}/status`) without blocking HTTP clients.
   - Graph exploration (`/nodes`, `/edges`, `/impact`) and semantic search (`/search`) operate as synchronous read endpoints.

2. **Mandatory Confidence, Provenance, & Evidence Fields**:
   - API response contracts (`cig/api/schemas.py`) enforce explicit `confidence` scores (bounded `[0.0, 1.0]`), `provenance` metadata (`file_path`, `source_span`), and model `evidence` payloads on all annotation responses.

3. **Dependency Injection & Clean Testability**:
   - Storage adapter and search engine instances are injected via FastAPI dependencies (`cig/api/dependencies.py`), enabling seamless dependency overrides during testing (`app.dependency_overrides`).






