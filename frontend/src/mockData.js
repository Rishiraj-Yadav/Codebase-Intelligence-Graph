// Canonical CIG Taxonomies & Offline Fallback Dataset

export const INTENT_TAXONOMY = [
  'authentication',
  'data processing',
  'API communication',
  'business logic',
  'database',
  'UI rendering',
  'testing',
  'configuration',
  'error handling',
  'caching',
  'logging',
  'file I/O',
  'machine learning',
  'messaging',
  'utility'
];

export const SMELL_TAXONOMY = [
  'god function',
  'misleading name',
  'dead code',
  'naming inconsistency',
  'comment-code mismatch'
];

export const INTENT_COLORS = {
  'authentication': '#EF4444',
  'data processing': '#3B82F6',
  'API communication': '#10B981',
  'business logic': '#F59E0B',
  'database': '#8B5CF6',
  'UI rendering': '#EC4899',
  'testing': '#6B7280',
  'configuration': '#6366F1',
  'error handling': '#DC2626',
  'caching': '#14B8A6',
  'logging': '#9CA3AF',
  'file I/O': '#D97706',
  'machine learning': '#06B6D4',
  'messaging': '#A855F7',
  'utility': '#64748B'
};

export const MOCK_NODES = [
  {
    id: 'cig.api.auth.verify_jwt',
    name: 'verify_jwt',
    node_type: 'function',
    file_path: 'cig/api/auth.py',
    source_span: { start_line: 14, start_column: 0, end_line: 48, end_column: 24 },
    docstring: 'Decode and validate JSON Web Token signatures with RSA public keys.',
    code_snippet: `def verify_jwt(token: str, secret_key: str) -> Dict[str, Any]:\n    """Decode and validate JSON Web Token signatures with RSA public keys."""\n    try:\n        payload = jwt.decode(token, secret_key, algorithms=["RS256"])\n        if payload.get("exp") < time.time():\n            raise TokenExpiredError("Token expired")\n        return payload\n    except Exception as e:\n        logger.error(f"JWT verification failed: {e}")\n        raise AuthenticationError("Invalid authentication credentials")`,
    annotations: {
      summary: 'Decodes JWT token string using secret key and verifies expiration timestamp.',
      summary_confidence: 0.94,
      doc_quality_score: 0.88,
      doc_feedback: 'Clear docstring explaining decoding and algorithm assumptions. Param types annotated.',
      doc_score_confidence: 0.91,
      intent_labels: ['authentication', 'error handling'],
      intent_confidence: 0.96,
      smell_labels: [],
      smell_probabilities: {
        'god function': 0.05,
        'misleading name': 0.02,
        'dead code': 0.01,
        'naming inconsistency': 0.04,
        'comment-code mismatch': 0.03
      },
      smell_confidence: 0.95
    }
  },
  {
    id: 'cig.storage.neo4j_adapter.Neo4jAdapter',
    name: 'Neo4jAdapter',
    node_type: 'class',
    file_path: 'cig/storage/neo4j_adapter.py',
    source_span: { start_line: 25, start_column: 0, end_line: 185, end_column: 0 },
    docstring: 'Neo4j Bolt database driver wrapper for Cypher query execution and graph traversal.',
    code_snippet: `class Neo4jAdapter:\n    """Neo4j Bolt database driver wrapper for Cypher query execution and graph traversal."""\n    def __init__(self, uri: str, auth: Tuple[str, str]):\n        self.driver = GraphDatabase.driver(uri, auth=auth)\n\n    def query(self, cypher: str, params: Dict[str, Any] = None) -> List[Dict]:\n        with self.driver.session() as session:\n            return session.run(cypher, params or {}).data()`,
    annotations: {
      summary: 'Manages Neo4j database sessions, connection pooling, and Cypher transaction execution.',
      summary_confidence: 0.92,
      doc_quality_score: 0.75,
      doc_feedback: 'Class level docstring present. Individual query methods lack complete parameter type specs.',
      doc_score_confidence: 0.89,
      intent_labels: ['database', 'business logic'],
      intent_confidence: 0.93,
      smell_labels: ['god function'],
      smell_probabilities: {
        'god function': 0.82,
        'misleading name': 0.12,
        'dead code': 0.03,
        'naming inconsistency': 0.15,
        'comment-code mismatch': 0.08
      },
      smell_confidence: 0.87
    }
  },
  {
    id: 'cig.retrieval.search.CodebaseSearchEngine',
    name: 'CodebaseSearchEngine',
    node_type: 'class',
    file_path: 'cig/retrieval/search.py',
    source_span: { start_line: 18, start_column: 0, end_line: 110, end_column: 0 },
    docstring: 'Hybrid semantic and graph retrieval search engine using UniXcoder embeddings and Qdrant.',
    code_snippet: `class CodebaseSearchEngine:\n    """Hybrid semantic and graph retrieval search engine using UniXcoder embeddings."""\n    def search(self, query: str, top_k: int = 5, intent_filter: str = None) -> Dict[str, Any]:\n        query_vec = self.encoder.encode(query)\n        vec_results = self.qdrant.search(collection="cig_nodes", vector=query_vec, limit=top_k)\n        return self._re_rank(vec_results, intent_filter)`,
    annotations: {
      summary: 'Executes natural language semantic code search queries via UniXcoder vector embeddings and reranking.',
      summary_confidence: 0.95,
      doc_quality_score: 0.92,
      doc_feedback: 'Comprehensive docstring with vector indexing details and return schema specs.',
      doc_score_confidence: 0.95,
      intent_labels: ['machine learning', 'data processing', 'database'],
      intent_confidence: 0.98,
      smell_labels: [],
      smell_probabilities: {
        'god function': 0.18,
        'misleading name': 0.05,
        'dead code': 0.02,
        'naming inconsistency': 0.06,
        'comment-code mismatch': 0.04
      },
      smell_confidence: 0.94
    }
  },
  {
    id: 'cig.pipelines.pipeline.orchestrate_ingestion',
    name: 'orchestrate_ingestion',
    node_type: 'function',
    file_path: 'cig/pipelines/pipeline.py',
    source_span: { start_line: 45, start_column: 0, end_line: 230, end_column: 0 },
    docstring: 'Runs end-to-end repository parsing, model inference (M1-M5), and graph database persistence.',
    code_snippet: `def orchestrate_ingestion(repo_path: str) -> Dict[str, Any]:\n    # Parsers code, calls M1, M2, M3, M4, M5, writes to Neo4j & Qdrant, updates redis logs...\n    ast_tree = parse_repository(repo_path)\n    for node in ast_tree.nodes:\n        sum_res = run_m1_t5(node)\n        doc_res = run_m2_bert(node)\n        intent_res = run_m3_intent(node)\n        smell_res = run_m4_smell(node)\n        save_node(node, sum_res, doc_res, intent_res, smell_res)\n    return {"status": "SUCCESS", "nodes": len(ast_tree.nodes)}`,
    annotations: {
      summary: 'Main orchestration monolith executing parsing, NLP feature extraction, edge label analysis, and DB updates.',
      summary_confidence: 0.89,
      doc_quality_score: 0.35,
      doc_feedback: 'Docstring fails to document exceptions thrown. Function length > 180 lines doing 7 distinct tasks.',
      doc_score_confidence: 0.91,
      intent_labels: ['business logic', 'data processing', 'machine learning', 'database', 'logging'],
      intent_confidence: 0.88,
      smell_labels: ['god function', 'comment-code mismatch'],
      smell_probabilities: {
        'god function': 0.94,
        'misleading name': 0.38,
        'dead code': 0.12,
        'naming inconsistency': 0.45,
        'comment-code mismatch': 0.78
      },
      smell_confidence: 0.91
    }
  },
  {
    id: 'cig.parser.tree_sitter_parser.parse_file',
    name: 'parse_file',
    node_type: 'function',
    file_path: 'cig/parser/tree_sitter_parser.py',
    source_span: { start_line: 30, start_column: 0, end_line: 75, end_column: 0 },
    docstring: 'Parse source file using Tree-sitter AST parser into AST nodes and span ranges.',
    code_snippet: `def parse_file(file_path: str) -> List[BaseNode]:\n    """Parse source file using Tree-sitter AST parser into AST nodes."""\n    with open(file_path, 'r', encoding='utf-8') as f:\n        code = f.read()\n    tree = parser.parse(bytes(code, 'utf8'))\n    return extract_symbols(tree.root_node, file_path)`,
    annotations: {
      summary: 'Reads source file content from disk and invokes Tree-sitter parser to extract syntax AST nodes.',
      summary_confidence: 0.93,
      doc_quality_score: 0.82,
      doc_feedback: 'Well formatted docstring. Input parameter types clear.',
      doc_score_confidence: 0.90,
      intent_labels: ['file I/O', 'data processing'],
      intent_confidence: 0.95,
      smell_labels: [],
      smell_probabilities: {
        'god function': 0.08,
        'misleading name': 0.04,
        'dead code': 0.02,
        'naming inconsistency': 0.05,
        'comment-code mismatch': 0.03
      },
      smell_confidence: 0.96
    }
  },
  {
    id: 'cig.models.m1_summarizer.summarize_code',
    name: 'summarize_code',
    node_type: 'function',
    file_path: 'cig/models/m1_summarizer.py',
    source_span: { start_line: 20, start_column: 0, end_line: 52, end_column: 0 },
    docstring: 'Generate natural language summary using fine-tuned CodeT5 model.',
    code_snippet: `def summarize_code(code_str: str) -> M1CodeSummarizerOutput:\n    """Generate natural language summary using fine-tuned CodeT5 model."""\n    inputs = tokenizer(code_str, return_tensors="pt", truncation=True, max_length=512)\n    summary_ids = model.generate(inputs["input_ids"], max_length=64)\n    decoded = tokenizer.decode(summary_ids[0], skip_special_tokens=True)\n    return M1CodeSummarizerOutput(summary=decoded, confidence=0.91)`,
    annotations: {
      summary: 'Executes CodeT5 sequence-to-sequence model inference to generate code docstring summaries.',
      summary_confidence: 0.96,
      doc_quality_score: 0.90,
      doc_feedback: 'Docstring accurately reflects CodeT5 inference routine and output contract.',
      doc_score_confidence: 0.94,
      intent_labels: ['machine learning', 'utility'],
      intent_confidence: 0.97,
      smell_labels: [],
      smell_probabilities: {
        'god function': 0.04,
        'misleading name': 0.02,
        'dead code': 0.01,
        'naming inconsistency': 0.03,
        'comment-code mismatch': 0.02
      },
      smell_confidence: 0.97
    }
  },
  {
    id: 'cig.models.m4_smell_detector.detect_smells',
    name: 'detect_smells',
    node_type: 'function',
    file_path: 'cig/models/m4_smell_detector.py',
    source_span: { start_line: 18, start_column: 0, end_line: 60, end_column: 0 },
    docstring: 'Predict multi-label code smells using GraphCodeBERT classification head.',
    code_snippet: `def detect_smells(code_str: str, ast_metrics: Dict) -> M4SmellDetectorOutput:\n    """Predict multi-label code smells using GraphCodeBERT classification head."""\n    logits = smell_head(encoder(code_str))\n    probs = torch.sigmoid(logits)\n    detected = [SMELL_TAXONOMY[i] for i, p in enumerate(probs) if p > 0.5]\n    return M4SmellDetectorOutput(smell_labels=detected, smell_probabilities=dict(zip(SMELL_TAXONOMY, probs)))`,
    annotations: {
      summary: 'Passes AST graph structure and token sequence through GraphCodeBERT multi-label classifier for code smell scoring.',
      summary_confidence: 0.91,
      doc_quality_score: 0.85,
      doc_feedback: 'Clear docstring specifying GraphCodeBERT classification logic.',
      doc_score_confidence: 0.88,
      intent_labels: ['machine learning', 'testing'],
      intent_confidence: 0.92,
      smell_labels: [],
      smell_probabilities: {
        'god function': 0.07,
        'misleading name': 0.03,
        'dead code': 0.02,
        'naming inconsistency': 0.05,
        'comment-code mismatch': 0.04
      },
      smell_confidence: 0.93
    }
  },
  {
    id: 'cig.api.routes.graph.get_node_impact',
    name: 'get_node_impact',
    node_type: 'function',
    file_path: 'cig/api/routes/graph.py',
    source_span: { start_line: 69, start_column: 0, end_line: 90, end_column: 0 },
    docstring: 'Traverse graph downstream up to max_hops from root node to assess architectural impact.',
    code_snippet: `@router.get("/nodes/{node_id:path}/impact")\ndef get_node_impact(node_id: str, max_hops: int = 3, adapter = Depends(get_neo4j_adapter)):\n    root = adapter.get_node_by_id(node_id)\n    if not root: raise HTTPException(404, "Node not found")\n    downstream = adapter.get_impact_analysis(node_id, max_hops)\n    return ImpactAnalysisResponse(root_node_id=node_id, max_hops=max_hops, downstream_nodes=downstream)`,
    annotations: {
      summary: 'FastAPI route endpoint returning graph reachability analysis for architectural impact assessment.',
      summary_confidence: 0.95,
      doc_quality_score: 0.88,
      doc_feedback: 'Endpoint signature clear with Pydantic response models specified.',
      doc_score_confidence: 0.92,
      intent_labels: ['API communication', 'business logic'],
      intent_confidence: 0.96,
      smell_labels: [],
      smell_probabilities: {
        'god function': 0.06,
        'misleading name': 0.03,
        'dead code': 0.01,
        'naming inconsistency': 0.04,
        'comment-code mismatch': 0.02
      },
      smell_confidence: 0.95
    }
  },
  {
    id: 'cig.utils.config.load_env_config',
    name: 'load_env_config',
    node_type: 'function',
    file_path: 'cig/utils/config.py',
    source_span: { start_line: 10, start_column: 0, end_line: 35, end_column: 0 },
    docstring: 'Load environment variables and parse application settings.',
    code_snippet: `def load_env_config() -> Settings:\n    """Load environment variables and parse application settings."""\n    env_file = os.getenv("ENV_FILE", ".env")\n    return Settings(_env_file=env_file)`,
    annotations: {
      summary: 'Parses environment variables and returns pydantic Settings singleton.',
      summary_confidence: 0.97,
      doc_quality_score: 0.70,
      doc_feedback: 'Basic summary present, missing detail on fallback defaults.',
      doc_score_confidence: 0.85,
      intent_labels: ['configuration', 'utility'],
      intent_confidence: 0.95,
      smell_labels: ['naming inconsistency'],
      smell_probabilities: {
        'god function': 0.02,
        'misleading name': 0.15,
        'dead code': 0.04,
        'naming inconsistency': 0.65,
        'comment-code mismatch': 0.12
      },
      smell_confidence: 0.86
    }
  },
  {
    id: 'cig.utils.cache.RedisCacheManager',
    name: 'RedisCacheManager',
    node_type: 'class',
    file_path: 'cig/utils/cache.py',
    source_span: { start_line: 12, start_column: 0, end_line: 60, end_column: 0 },
    docstring: 'Async Redis cache helper for caching model inference outputs.',
    code_snippet: `class RedisCacheManager:\n    """Async Redis cache helper for caching model inference outputs."""\n    def __init__(self, redis_url: str):\n        self.client = redis.from_url(redis_url)\n    async def get(self, key: str) -> Optional[str]:\n        return await self.client.get(key)`,
    annotations: {
      summary: 'Provides async getter and setter interface over Redis key-value store for inference output caching.',
      summary_confidence: 0.93,
      doc_quality_score: 0.82,
      doc_feedback: 'Class docstring present. Async method signatures clear.',
      doc_score_confidence: 0.89,
      intent_labels: ['caching', 'utility'],
      intent_confidence: 0.94,
      smell_labels: [],
      smell_probabilities: {
        'god function': 0.05,
        'misleading name': 0.04,
        'dead code': 0.02,
        'naming inconsistency': 0.05,
        'comment-code mismatch': 0.03
      },
      smell_confidence: 0.92
    }
  },
  {
    id: 'cig.messaging.queue.publish_task',
    name: 'publish_task',
    node_type: 'function',
    file_path: 'cig/messaging/queue.py',
    source_span: { start_line: 15, start_column: 0, end_line: 40, end_column: 0 },
    docstring: 'Publish asynchronous background job event payload to RabbitMQ message exchange.',
    code_snippet: `def publish_task(routing_key: str, payload: Dict[str, Any]) -> None:\n    """Publish background job payload to RabbitMQ exchange."""\n    channel.basic_publish(\n        exchange='cig_events',\n        routing_key=routing_key,\n        body=json.dumps(payload)\n    )`,
    annotations: {
      summary: 'Encodes job payload into JSON and publishes message to RabbitMQ exchange topic.',
      summary_confidence: 0.91,
      doc_quality_score: 0.78,
      doc_feedback: 'Docstring clear on message bus interaction.',
      doc_score_confidence: 0.87,
      intent_labels: ['messaging', 'API communication'],
      intent_confidence: 0.93,
      smell_labels: ['dead code'],
      smell_probabilities: {
        'god function': 0.06,
        'misleading name': 0.10,
        'dead code': 0.71,
        'naming inconsistency': 0.08,
        'comment-code mismatch': 0.15
      },
      smell_confidence: 0.84
    }
  },
  {
    id: 'cig.utils.deprecated_helper.calculate_legacy_metrics',
    name: 'calculate_legacy_metrics',
    node_type: 'function',
    file_path: 'cig/utils/deprecated_helper.py',
    source_span: { start_line: 5, start_column: 0, end_line: 30, end_column: 0 },
    docstring: 'Compute AST complexity metric (deprecated in v2.0).',
    code_snippet: `def calculate_legacy_metrics(node):\n    # DEPRECATED: Do not use. Use tree-sitter node depth instead.\n    # Computes cyclomatic complexity\n    pass`,
    annotations: {
      summary: 'Legacy cyclomatic complexity calculation stub left in codebase without active callers.',
      summary_confidence: 0.88,
      doc_quality_score: 0.25,
      doc_feedback: 'Docstring warns of deprecation, function body contains no active implementation.',
      doc_score_confidence: 0.90,
      intent_labels: ['utility'],
      intent_confidence: 0.85,
      smell_labels: ['dead code', 'misleading name'],
      smell_probabilities: {
        'god function': 0.02,
        'misleading name': 0.68,
        'dead code': 0.92,
        'naming inconsistency': 0.30,
        'comment-code mismatch': 0.55
      },
      smell_confidence: 0.91
    }
  }
];

export const MOCK_EDGES = [
  {
    id: 'edge_1',
    source_id: 'cig.pipelines.pipeline.orchestrate_ingestion',
    target_id: 'cig.parser.tree_sitter_parser.parse_file',
    edge_type: 'calls',
    annotations: {
      label: 'parses repository source files',
      confidence: 0.95,
      explanation: 'orchestrate_ingestion invokes parse_file to generate initial AST node trees before inference.'
    }
  },
  {
    id: 'edge_2',
    source_id: 'cig.pipelines.pipeline.orchestrate_ingestion',
    target_id: 'cig.models.m1_summarizer.summarize_code',
    edge_type: 'calls',
    annotations: {
      label: 'requests CodeT5 summarization',
      confidence: 0.92,
      explanation: 'Passes AST function node code string into summarize_code to create M1 natural language summaries.'
    }
  },
  {
    id: 'edge_3',
    source_id: 'cig.pipelines.pipeline.orchestrate_ingestion',
    target_id: 'cig.models.m4_smell_detector.detect_smells',
    edge_type: 'calls',
    annotations: {
      label: 'evaluates multi-label code smells',
      confidence: 0.90,
      explanation: 'Sends AST structural features to detect_smells to run GraphCodeBERT smell classification head.'
    }
  },
  {
    id: 'edge_4',
    source_id: 'cig.pipelines.pipeline.orchestrate_ingestion',
    target_id: 'cig.storage.neo4j_adapter.Neo4jAdapter',
    edge_type: 'instantiates',
    annotations: {
      label: 'persists AST graph data',
      confidence: 0.97,
      explanation: 'Instantiates Neo4jAdapter database driver session to write nodes, edges, and model annotations.'
    }
  },
  {
    id: 'edge_5',
    source_id: 'cig.retrieval.search.CodebaseSearchEngine',
    target_id: 'cig.storage.neo4j_adapter.Neo4jAdapter',
    edge_type: 'calls',
    annotations: {
      label: 'fetches graph node attributes',
      confidence: 0.94,
      explanation: 'Queries Neo4jAdapter to retrieve detailed node metadata for top-k vector search results.'
    }
  },
  {
    id: 'edge_6',
    source_id: 'cig.api.routes.graph.get_node_impact',
    target_id: 'cig.storage.neo4j_adapter.Neo4jAdapter',
    edge_type: 'calls',
    annotations: {
      label: 'traverses downstream dependencies',
      confidence: 0.96,
      explanation: 'Calls get_impact_analysis on Neo4jAdapter to retrieve graph reachability up to max_hops.'
    }
  },
  {
    id: 'edge_7',
    source_id: 'cig.api.auth.verify_jwt',
    target_id: 'cig.utils.config.load_env_config',
    edge_type: 'calls',
    annotations: {
      label: 'reads JWT secret configuration',
      confidence: 0.89,
      explanation: 'Retrieves active JWT secret key and token expiration parameters from load_env_config.'
    }
  },
  {
    id: 'edge_8',
    source_id: 'cig.retrieval.search.CodebaseSearchEngine',
    target_id: 'cig.utils.cache.RedisCacheManager',
    edge_type: 'calls',
    annotations: {
      label: 'caches query vector results',
      confidence: 0.91,
      explanation: 'Checks RedisCacheManager for cached search query vector embeddings before re-encoding.'
    }
  },
  {
    id: 'edge_9',
    source_id: 'cig.pipelines.pipeline.orchestrate_ingestion',
    target_id: 'cig.messaging.queue.publish_task',
    edge_type: 'calls',
    annotations: {
      label: 'publishes job progress status',
      confidence: 0.88,
      explanation: 'Emits Celery task execution progress notifications to RabbitMQ message bus.'
    }
  },
  {
    id: 'edge_10',
    source_id: 'cig.pipelines.pipeline.orchestrate_ingestion',
    target_id: 'cig.utils.deprecated_helper.calculate_legacy_metrics',
    edge_type: 'calls',
    annotations: {
      label: 'legacy metric calculation (dead code path)',
      confidence: 0.70,
      explanation: 'Outdated call path triggering legacy metric calculation.'
    }
  }
];

export const MOCK_IMPACT_MAP = {
  'cig.pipelines.pipeline.orchestrate_ingestion': [
    { node_id: 'cig.parser.tree_sitter_parser.parse_file', distance: 1, path: ['cig.pipelines.pipeline.orchestrate_ingestion', 'cig.parser.tree_sitter_parser.parse_file'] },
    { node_id: 'cig.models.m1_summarizer.summarize_code', distance: 1, path: ['cig.pipelines.pipeline.orchestrate_ingestion', 'cig.models.m1_summarizer.summarize_code'] },
    { node_id: 'cig.models.m4_smell_detector.detect_smells', distance: 1, path: ['cig.pipelines.pipeline.orchestrate_ingestion', 'cig.models.m4_smell_detector.detect_smells'] },
    { node_id: 'cig.storage.neo4j_adapter.Neo4jAdapter', distance: 1, path: ['cig.pipelines.pipeline.orchestrate_ingestion', 'cig.storage.neo4j_adapter.Neo4jAdapter'] },
    { node_id: 'cig.messaging.queue.publish_task', distance: 1, path: ['cig.pipelines.pipeline.orchestrate_ingestion', 'cig.messaging.queue.publish_task'] },
    { node_id: 'cig.retrieval.search.CodebaseSearchEngine', distance: 2, path: ['cig.pipelines.pipeline.orchestrate_ingestion', 'cig.storage.neo4j_adapter.Neo4jAdapter', 'cig.retrieval.search.CodebaseSearchEngine'] },
    { node_id: 'cig.api.routes.graph.get_node_impact', distance: 2, path: ['cig.pipelines.pipeline.orchestrate_ingestion', 'cig.storage.neo4j_adapter.Neo4jAdapter', 'cig.api.routes.graph.get_node_impact'] }
  ],
  'cig.storage.neo4j_adapter.Neo4jAdapter': [
    { node_id: 'cig.retrieval.search.CodebaseSearchEngine', distance: 1, path: ['cig.storage.neo4j_adapter.Neo4jAdapter', 'cig.retrieval.search.CodebaseSearchEngine'] },
    { node_id: 'cig.api.routes.graph.get_node_impact', distance: 1, path: ['cig.storage.neo4j_adapter.Neo4jAdapter', 'cig.api.routes.graph.get_node_impact'] }
  ]
};
