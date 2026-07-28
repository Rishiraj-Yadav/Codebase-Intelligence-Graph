# Codebase Intelligence Graph (CIG)

A semantic code-understanding system that parses code repositories into typed structural graphs, enriches nodes and edges with specialized NLP models, stores graph data in Neo4j, supports dense vector retrieval via FAISS, and exposes interactive graph exploration through FastAPI and a React + D3.js dashboard.

---

## Architecture Overview

```
                      +-----------------------------+
                      |   Source Code Repository    |
                      +--------------+--------------+
                                     |
                                     v
                      +-----------------------------+
                      | Tree-sitter Parsing Engine  |
                      +--------------+--------------+
                                     |
                                     v
                      +-----------------------------+
                      |   Structural Graph Builder  |
                      | (Functions, Classes, Edges) |
                      +--------------+--------------+
                                     |
                                     v
                      +-----------------------------+
                      |  5 Specialized NLP Models   |
                      |  (M1, M2, M3, M4, M5)       |
                      +--------------+--------------+
                                     |
             +-----------------------+-----------------------+
             |                                               |
             v                                               v
+--------------------------+                   +---------------------------+
| Neo4j Graph Database     |                   | FAISS Vector Index        |
| (Cypher Graph Queries)   |                   | (UniXcoder Embeddings)    |
+------------+-------------+                   +-------------+-------------+
             |                                               |
             +-----------------------+-----------------------+
                                     |
                                     v
                      +-----------------------------+
                      | FastAPI REST & Search API   |
                      +--------------+--------------+
                                     |
                                     v
                      +-----------------------------+
                      | React + D3.js + Tailwind UI |
                      +-----------------------------+
```

---

## Key Features

- **AST Parsing Engine**: Tree-sitter powered Python parser extracting `Function`, `Class`, and `Module` nodes with exact line/column source spans and signatures.
- **Structural Relations**: Extracts `calls`, `imports`, `inherits`, and `instantiates` edges.
- **5 Specialized NLP Intelligence Models**:
  - **M1 (CodeT5)**: Natural language function & class summaries.
  - **M2 (CodeBERT Scorer)**: Documentation quality score (0–100) and improvement feedback.
  - **M3 (CodeBERT Intent)**: Multi-label classification across 15 intent categories (`authentication`, `database`, `API communication`, etc.).
  - **M4 (GraphCodeBERT Smell Detector)**: Probability predictions across 5 code smells (`god function`, `dead code`, `naming inconsistency`, etc.).
  - **M5 (DeBERTa Cross-Encoder)**: Semantic relation labeling & confidence scoring for structural call edges.
- **Graph Storage (Neo4j)**: Persistent storage for graph nodes, edges, and model annotations with Cypher query support.
- **Semantic Retrieval (FAISS)**: 768-dim UniXcoder dense embeddings with fast inner-product similarity search.
- **Asynchronous Task Processing**: Celery task queue powered by Redis for non-blocking repository ingestion.
- **Interactive D3.js Visual Dashboard**: React frontend featuring force-directed graph canvas, multi-label intent coloring, documentation quality borders, smell pulsing animations, slide-over inspector drawer, natural language search, composable filter panel, and $N$-hop impact analysis traversal.

---

## Required Tech Stack

- **Python**: 3.10+
- **Backend Framework**: FastAPI, Uvicorn
- **Task Queue & Broker**: Celery, Redis
- **Parsing**: Tree-sitter
- **Machine Learning**: PyTorch, HuggingFace Transformers, NLTK, Scipy, Scikit-Learn, Weights & Biases
- **Vector Store**: FAISS (`faiss-cpu`)
- **Graph Database**: Neo4j 5 Community Edition
- **Frontend**: React, D3.js, TailwindCSS, Lucide Icons, Vite

---

## Prerequisites

Before starting, ensure you have installed:
1. **Python**: Version 3.10 or higher
2. **Node.js**: Version 18 or higher (with `npm`)
3. **Docker Desktop** (or Docker Engine with `docker-compose`)

---

## Installation Guide

### 1. Clone the Repository

```bash
git clone https://github.com/Rishiraj-Yadav/Codebase-Intelligence-Graph.git
cd Codebase-Intelligence-Graph
```

### 2. Set Up Python Virtual Environment

```bash
# Windows
python -m venv venv
venv\Scripts\activate

# Linux / macOS
python3 -m venv venv
source venv/bin/activate
```

### 3. Install Python Dependencies

```bash
pip install -r requirements.txt
```

### 4. Install Frontend Dependencies

```bash
cd frontend
npm install
cd ..
```

---

## Quick Start Guide to Run the Project

Running CIG requires starting the database services, backend API, Celery worker, and frontend.

### Step 1: Start Docker Services (Neo4j & Redis)

In your main terminal, run:

```bash
docker-compose up -d
```

* **Neo4j Web HTTP**: [http://localhost:7474](http://localhost:7474) (Credentials: `neo4j` / `password`)
* **Neo4j Bolt**: `bolt://localhost:7687`
* **Redis**: `localhost:6379`

---

### Step 2: Start the FastAPI Backend API

Open **Terminal 1** at project root (`Codebase-Intelligence-Graph`) and run:

```bash
python -m uvicorn cig.api.main:app --reload --port 8000
```

* **Backend URL**: [http://localhost:8000](http://localhost:8000)
* **Interactive OpenAPI Docs**: [http://localhost:8000/docs](http://localhost:8000/docs)

---

### Step 3: Start the Celery Worker

Open **Terminal 2** at project root (`Codebase-Intelligence-Graph`) and run:

```bash
python -m celery -A cig.pipelines.celery_tasks.celery_app worker --loglevel=info -P solo
```

---

### Step 4: Start the Frontend Web UI

Open **Terminal 3**, navigate to `frontend`, and run:

```bash
cd frontend
npm run dev
```

* **Frontend Dashboard**: Open your browser at **[http://localhost:3000](http://localhost:3000)** (or `http://localhost:5173`).

---

## How to Ingest & Analyze a Repository

You can ingest **any Python codebase** on your computer.

> **Important JSON Tip**: When supplying Windows paths in JSON, use **forward slashes (`/`)** (e.g. `"R:/my_project"`) to avoid JSON escape errors.

### Via Swagger Docs / REST API

1. Go to [http://localhost:8000/docs](http://localhost:8000/docs).
2. Expand `POST /ingest` and click **Try it out**.
3. Submit a JSON payload:

```json
{
  "repo_path": "C:/path/to/your/python_project",
  "ignore_patterns": ["*.pyc", "__pycache__", "venv"]
}
```

### Via cURL

```bash
curl -X POST "http://localhost:8000/ingest" \
     -H "Content-Type: application/json" \
     -d '{
           "repo_path": "C:/path/to/your/python_project",
           "ignore_patterns": ["*.pyc", "__pycache__", "venv"]
         }'
```

### Via Python Script

```python
from cig.pipelines.ingestion_pipeline import IngestionPipeline

pipeline = IngestionPipeline()
summary = pipeline.run(repo_path="C:/path/to/your/python_project")
print(summary)
```

---

## Exploring the Frontend Dashboard (`http://localhost:3000`)

- **Interactive D3 Force Graph**: Nodes represent functions/classes/modules. Size indicates code length, color represents intent category, border color represents documentation quality, and a pulsing red border highlights code smells.
- **Natural Language Search Bar**: Enter queries like `"how is authentication implemented?"` to rank components using dense UniXcoder similarity search.
- **Slide-Over Detail Inspector**: Click any graph node to inspect summaries, doc quality scores, intent labels, smell probabilities, source code snippets, and connected edges.
- **Impact Analysis**: Click **Show Impact Analysis** on any node to visually highlight all downstream dependencies up to $N$ hops deep.
- **Filter Panel**: Filter graph nodes by Intent Taxonomy, Code Smell type, Doc Quality score range, or File Path.

---

## Running Evaluation Suites & Tests

### Run Full Test Suite (121 Tests)

```bash
pytest
```

### Run Model Evaluation Benchmarks

```bash
# M1 CodeT5 Summarizer (BLEU-4)
python evals/eval_m1.py

# M2 CodeBERT Scorer (Spearman Correlation)
python evals/eval_m2.py

# M3 CodeBERT Intent Classifier (Macro F1)
python evals/eval_m3.py

# M4 GraphCodeBERT Smell Detector (AUC-ROC)
python evals/eval_m4.py

# M5 DeBERTa Edge Labeler (Accuracy)
python evals/eval_m5.py

# End-to-End Pipeline Smoke Test
python evals/pipeline_smoke_test.py
```

---

## Project Layout

```text
CIG/
├── cig/                         # Core Python Package
│   ├── graph_schema/            # Pydantic node/edge/annotation contracts
│   ├── parser/                  # Tree-sitter parsing & AST extraction
│   ├── storage/                 # Neo4j adapter & Cypher query definitions
│   ├── models/                  # M1-M5 NLP inference interfaces & mock models
│   ├── retrieval/               # UniXcoder embedder & FAISS index search engine
│   ├── pipelines/               # Ingestion pipeline & Celery task definitions
│   └── api/                     # FastAPI app, schemas, dependencies & routers
├── evals/                       # Model evaluation scripts (M1-M5) & smoke test
├── frontend/                    # React + D3.js + TailwindCSS Web Application
│   ├── src/
│   │   ├── components/          # GraphViewer, NodeDrawer, FilterBar, SearchBox
│   │   ├── api/client.js        # REST client with offline mock fallback
│   │   └── App.jsx              # Main UI layout shell
│   └── package.json
├── tests/                       # Unit & integration pytest test suite (121 tests)
├── docker-compose.yml           # Neo4j & Redis service orchestrator
└── README.md                    # Project documentation
```

---

## License

Distributed under the MIT License. See `LICENSE` for details.
