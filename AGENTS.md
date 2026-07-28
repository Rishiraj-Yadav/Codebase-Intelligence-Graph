# AGENTS.md

This repository builds the Codebase Intelligence Graph (CIG).

CIG is a semantic code-understanding system that:

- parses repositories into a typed structural graph
- enriches nodes and edges with five specialized NLP models
- stores graph data and annotations in Neo4j
- supports semantic retrieval with embeddings plus FAISS
- exposes graph exploration and natural-language querying through an API and UI

## Required Tech Stack

Use this stack unless the user explicitly approves a change:

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

## Follow These Rules

- Treat this as a modular ML plus graph plus product system, not a generic app.
- Keep parsing, model inference, retrieval, storage, API, and frontend concerns separated.
- Prefer typed contracts between layers.
- Use the required tech stack as the default architecture for new files, docs, prompts, and subagent work.
- Preserve explainability: scores, labels, provenance, and evidence should remain visible.
- Treat model outputs as annotations with confidence, not ground truth.
- Keep training-time workflows separate from runtime inference code.
- Do not silently change label taxonomies, graph schema, or evaluation assumptions.

## Preferred Build Order

1. Graph schema and typed contracts
2. Parsing and AST extraction
3. Structural graph construction
4. Neo4j persistence and graph queries
5. Model inference interfaces
6. Retrieval and FAISS indexing
7. API endpoints
8. Frontend graph exploration
9. Training and evaluation refinement

## Stack-Specific Defaults

- Use Python for parsing, backend services, ML, retrieval, and evaluation code.
- Use FastAPI for HTTP APIs and Pydantic-style schemas for request and response contracts.
- Use Celery with Redis for long-running repository ingestion, model inference, indexing, and persistence jobs.
- Use Neo4j Community Edition for graph persistence and Cypher queries.
- Use FAISS for local vector search, with deterministic fallback behavior for tests.
- Use HuggingFace Transformers and PyTorch for model training and inference.
- Use PEFT/LoRA where fine-tuning full base models is too expensive.
- Use Weights & Biases for experiment tracking when training or evaluating models.
- Use React with D3.js and TailwindCSS for the graph exploration frontend.
- Use Docker Compose for local orchestration, Railway for backend deployment planning, and Vercel for frontend deployment planning.

## Local Codex Setup

- Repo-level Antigravity cli guidance is expanded in `.agnets/AGENTS.md`
- Reusable repo-local skills live in `.agents/skills/`
- Project subagents live in `.agnets/agents/`

## Use These Skills When Relevant

- `.agents/skills/planning-with-files`
- `.agents/skills/executing-plans`
- `.agents/skills/test-driven-development`
- `.agents/skills/verification-before-completion`
- `.agents/skills/user-context`

## Use These Subagents When Relevant

- `orchestrator`
- `workflow_manager`
- `research_agent`
- `api_designer`
- `parser_engineer`
- `graph_engineer`
- `ml_engineer`
- `eval_engineer`
- `backend_developer`
- `frontend_developer`
- `performance_optimizer`
- `fullstack_expert`

## Working Style

- Prefer thin end-to-end slices for early development.
- Write tests for schema, parsing, adapters, retrieval, and API contracts.
- Keep documentation aligned with architecture and model assumptions.
- If launched from the parent workspace, reference this project using the `NLP/` prefix.
