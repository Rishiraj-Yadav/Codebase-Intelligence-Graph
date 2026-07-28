This file defines project-specific Codex guidance for the Codebase Intelligence Graph (CIG) project.

# Project Identity

CIG is a semantic code understanding system, not a generic CRUD app.

The system takes a repository, parses it into a typed structural graph, enriches the graph with five trained NLP models, stores the result in Neo4j, supports semantic retrieval with embeddings plus FAISS, and exposes the output through an interactive graph UI and a query API.

Primary layers:

1. Parsing engine
2. NLP intelligence pipeline
3. RAG and retrieval layer
4. Knowledge graph storage and querying
5. Interactive frontend

# Required Tech Stack

Use this stack as the project default unless the user explicitly approves a change.

| Component | Technology |
| --- | --- |
| Code parsing | Tree-sitter with Python support first |
| NLP model training | HuggingFace Transformers, PyTorch, PEFT/LoRA |
| Base models | CodeT5, CodeBERT, GraphCodeBERT, DeBERTa, UniXcoder |
| Vector store | FAISS |
| Graph database | Neo4j Community Edition |
| Backend API | FastAPI, Celery, Redis |
| Frontend | React, D3.js, TailwindCSS |
| Experiment tracking | Weights & Biases |
| Deployment | Docker Compose, Railway for backend, Vercel for frontend |

Stack-specific defaults:

- Python is the default language for parsing, backend, ML, retrieval, and evaluation code.
- FastAPI is the default backend framework.
- Pydantic-style models should define API, graph, model-output, and job-status schemas.
- Celery plus Redis should handle long-running ingestion, enrichment, indexing, and persistence jobs.
- Neo4j Community Edition is the graph database target.
- FAISS is the vector index target, with deterministic test fallbacks where needed.
- HuggingFace Transformers and PyTorch are the default ML foundation.
- PEFT/LoRA should be preferred for affordable fine-tuning experiments.
- Weights & Biases should be used for experiment tracking in training and evaluation workflows.
- React, D3.js, and TailwindCSS are the frontend defaults.
- Docker Compose should support local development; Railway and Vercel should shape deployment docs and config.

# Core Product Goals

Every implementation decision should support one or more of these outcomes:

- Build a reliable typed graph from repository source code.
- Attach reproducible semantic annotations to nodes and edges.
- Keep each model independently trainable, testable, and replaceable.
- Make retrieval grounded in graph data and semantic embeddings.
- Expose the system through a usable API and an explainable interactive UI.

# Architecture Expectations

Treat the system as a modular pipeline with explicit contracts between stages.

Expected major domains:

- `parser` or `ingestion`: repository loading, language detection, AST extraction, symbol and relation extraction
- `graph_schema`: node and edge types, identifiers, metadata contracts
- `models`: training, inference, evaluation, checkpoints, label schemas
- `pipelines`: orchestration of parsing, enrichment, indexing, and persistence
- `retrieval`: embeddings, FAISS indexing, semantic search, grounding
- `storage`: Neo4j persistence, Cypher queries, graph projections
- `api`: endpoints for ingestion, graph exploration, node detail, search, and filtering
- `frontend`: graph rendering, filters, node details, search interactions
- `evals`: model metrics, pipeline validation, regression checks

Prefer clean boundaries between these layers. Do not tightly couple model internals to frontend or API code.

# Canonical CIG Semantics

Use this vocabulary consistently across code, docs, and design artifacts.

Node types:

- function
- class
- module

Structural edge types:

- calls
- imports
- inherits
- instantiates

Node annotations:

- summary
- documentation quality score
- documentation feedback
- intent labels
- smell labels
- smell probabilities

Edge annotations:

- semantic relation label
- confidence score
- human-readable explanation

Current model responsibilities:

- `M1`: Code summarizer using CodeT5
- `M2`: Documentation quality scorer using CodeBERT regression
- `M3`: Intent classifier using CodeBERT multi-label classification
- `M4`: Code smell detector using GraphCodeBERT multi-label classification
- `M5`: Semantic edge labeler using a DeBERTa cross-encoder

Intent taxonomy currently includes:

- authentication
- data processing
- API communication
- business logic
- database
- UI rendering
- testing
- configuration
- error handling
- caching
- logging
- file I/O
- machine learning
- messaging
- utility

Current smell taxonomy:

- god function
- misleading name
- dead code
- naming inconsistency
- comment-code mismatch

# Engineering Rules

- Preserve modularity. Each model should be trainable and evaluatable without rewriting the rest of the system.
- Prefer typed schemas for graph entities, model outputs, API payloads, and retrieval records.
- Use the required tech stack for new architecture, implementation, and documentation unless a task explicitly says otherwise.
- Keep the parsing layer deterministic where possible.
- Keep model inference side effects isolated from persistence logic.
- Separate training code from inference-serving code.
- Prefer reproducible data pipelines, versioned label schemas, and explicit metric reporting.
- Treat explainability as a feature, not a nice-to-have.
- Avoid magic prompt wrappers presented as semantic understanding. The product value comes from structured analysis plus specialized models.

# Evaluation Rules

When editing model or pipeline code, preserve or improve the documented targets:

- `M1` BLEU-4 `> 18`
- `M2` Spearman correlation `> 0.65`
- `M3` macro F1 `> 0.72`
- `M4` per-class AUC-ROC `> 0.80`
- `M5` classification accuracy `> 0.75`

If a change could affect metrics, add or update:

- dataset assumptions
- label schema notes
- evaluation scripts
- regression tests or smoke checks

# Preferred Build Order

Unless the user explicitly changes scope, default to this delivery order:

1. Graph schema and typed contracts
2. Repository ingestion and AST extraction
3. Structural graph construction
4. Persistence layer and Cypher access
5. Model inference interfaces and mock outputs
6. RAG indexing and semantic retrieval
7. API endpoints
8. Frontend visualization
9. Training and evaluation refinement

For early milestones, prefer end-to-end thin slices over isolated heavy components.

# Skills In This Repo

This project keeps reusable local skills under `.agents/skills/`.

When a task matches one of these skills, read its `SKILL.md` and follow it:

- `.agents/skills/executing-plans/SKILL.md`
- `.agents/skills/planning-with-files/SKILL.md`
- `.agents/skills/test-driven-development/SKILL.md`
- `.agents/skills/user-context/SKILL.md`
- `.agents/skills/verification-before-completion/SKILL.md`
- `.agents/skills/write-a-prd/SKILL.md`
- `.agents/skills/writing-plans/SKILL.md`

How to use them in this project:

- Use `planning-with-files` for phased implementation plans and architecture tracking.
- Use `executing-plans` when a plan already exists and work needs to be advanced incrementally.
- Use `test-driven-development` for parser, graph, retrieval, and API modules where behavior can be specified first.
- Use `verification-before-completion` before closing substantial implementation work.
- Use `user-context` to keep persistent project context and onboarding notes aligned.

# Subagents In This Repo

Project-local subagents live under `.agnets/agents/`.

Use them for focused workstreams:

- `orchestrator`: breaks down large CIG tasks and assigns phases
- `research_agent`: verifies papers, datasets, metrics, and model choices
- `workflow_manager`: plans datasets, training stages, evaluation flow, and milestone sequencing
- `api_designer`: defines clean contracts for ingestion, graph query, retrieval, and explainability endpoints
- `parser_engineer`: implements Tree-sitter parsing, AST extraction, source spans, and symbol IDs
- `graph_engineer`: designs Neo4j schema, Cypher queries, graph persistence, and impact analysis
- `ml_engineer`: implements HuggingFace, PyTorch, PEFT/LoRA model interfaces, inference, and training flows
- `eval_engineer`: owns BLEU, Spearman, F1, AUC-ROC, accuracy, and W&B evaluation reporting
- `backend_developer`: implements FastAPI, Celery, Redis, pipeline services, persistence, and orchestration glue
- `frontend_developer`: builds the React, D3.js, and TailwindCSS graph UI
- `performance_optimizer`: optimizes indexing, graph queries, retrieval latency, and UI scalability
- `fullstack_expert`: use only when a task truly spans API plus graph plus UI in one pass

Do not use subagents for trivial edits. Prefer them for scoped specialist tasks with clear boundaries.

# Task Routing Guidance

Choose the smallest specialist that matches the work:

- Dataset design, benchmarking, literature comparison -> `research_agent`
- API contracts, request and response schemas -> `api_designer`
- Tree-sitter parsing, AST extraction, source spans, symbol IDs -> `parser_engineer`
- Neo4j schema, Cypher queries, graph persistence, impact analysis -> `graph_engineer`
- HuggingFace, PyTorch, PEFT/LoRA, model inference/training -> `ml_engineer`
- BLEU, Spearman, F1, AUC-ROC, accuracy, W&B reporting -> `eval_engineer`
- FastAPI, Celery, Redis, ingestion services, orchestration code -> `backend_developer`
- React, D3.js, TailwindCSS, graph interactions, filtering UX -> `frontend_developer`
- Multi-phase planning and sequencing -> `workflow_manager`
- Cross-cutting project coordination -> `orchestrator`
- FAISS latency, Neo4j performance, Celery throughput, frontend graph rendering -> `performance_optimizer`

# Data And Model Hygiene

- Keep raw datasets, derived datasets, labels, checkpoints, and eval artifacts clearly separated.
- Never silently change label taxonomies.
- Prefer config-driven paths and experiment metadata over hardcoded file layouts.
- Record dataset provenance whenever adding synthetic or silver-labeled data.
- Distinguish training-time artifacts from runtime inference artifacts.

# API And UI Guidance

API design should expose explainable outputs, not just opaque scores.

Useful API capabilities for this project:

- ingest repository
- parse repository status
- list graph nodes and edges
- retrieve node detail with annotations
- semantic search over codebase
- filter by intent, smell, score range, and file path
- impact analysis for a node

Frontend guidance:

- prioritize clarity over visual novelty
- make node semantics readable
- show confidence and uncertainty explicitly
- make filters composable
- avoid hiding raw evidence behind only summaries

# Safety And Scope

- Do not claim semantic certainty where the models only provide probabilities.
- Keep explanations grounded in extracted code, graph structure, or model outputs.
- Treat generated summaries and labels as annotations, not ground truth.
- Flag assumptions when a repository language, framework, or dataset detail is missing.

# Practical Note

If Codex is launched from the `NLP` directory, these repo-local paths resolve naturally.
If it is launched from the parent workspace, prefer referencing files with the `NLP/` prefix when reading or editing project artifacts.
