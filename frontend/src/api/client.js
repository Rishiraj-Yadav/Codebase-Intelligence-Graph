import { MOCK_NODES, MOCK_EDGES, MOCK_IMPACT_MAP } from '../mockData';

const BASE_URL = 'http://localhost:8000';

export async function fetchNodes(filters = {}) {
  try {
    const params = new URLSearchParams();
    if (filters.node_type) params.append('node_type', filters.node_type);

    const response = await fetch(`${BASE_URL}/nodes?${params.toString()}`, {
      headers: { 'Accept': 'application/json' }
    });

    if (!response.ok) throw new Error(`HTTP ${response.status}`);
    const data = await response.json();
    return { data: data.nodes || [], isMock: false };
  } catch (err) {
    console.warn('Backend API connection failed, using mock nodes fallback:', err.message);
    return { data: MOCK_NODES, isMock: true, error: err.message };
  }
}

export async function fetchEdges(edgeType = null) {
  try {
    const params = new URLSearchParams();
    if (edgeType) params.append('edge_type', edgeType);

    const response = await fetch(`${BASE_URL}/edges?${params.toString()}`, {
      headers: { 'Accept': 'application/json' }
    });

    if (!response.ok) throw new Error(`HTTP ${response.status}`);
    const data = await response.json();
    return { data: data.edges || [], isMock: false };
  } catch (err) {
    console.warn('Backend API connection failed, using mock edges fallback:', err.message);
    return { data: MOCK_EDGES, isMock: true };
  }
}

export async function fetchNodeDetail(nodeId) {
  try {
    const encodedId = encodeURIComponent(nodeId);
    const response = await fetch(`${BASE_URL}/nodes/${encodedId}`, {
      headers: { 'Accept': 'application/json' }
    });

    if (!response.ok) throw new Error(`HTTP ${response.status}`);
    const data = await response.json();
    return { data: data.node, isMock: false };
  } catch (err) {
    console.warn(`Backend API detail failed for ${nodeId}, searching mock data:`, err.message);
    const mockNode = MOCK_NODES.find(n => n.id === nodeId) || MOCK_NODES[0];
    return { data: mockNode, isMock: true };
  }
}

export async function fetchImpactAnalysis(nodeId, maxHops = 3) {
  try {
    const encodedId = encodeURIComponent(nodeId);
    const response = await fetch(`${BASE_URL}/nodes/${encodedId}/impact?max_hops=${maxHops}`, {
      headers: { 'Accept': 'application/json' }
    });

    if (!response.ok) throw new Error(`HTTP ${response.status}`);
    const data = await response.json();
    return { data: data, isMock: false };
  } catch (err) {
    console.warn(`Backend API impact analysis failed for ${nodeId}, using mock impact:`, err.message);
    const mockImpact = MOCK_IMPACT_MAP[nodeId] || [
      { node_id: 'cig.retrieval.search.CodebaseSearchEngine', distance: 1, path: [nodeId, 'cig.retrieval.search.CodebaseSearchEngine'] },
      { node_id: 'cig.storage.neo4j_adapter.Neo4jAdapter', distance: 1, path: [nodeId, 'cig.storage.neo4j_adapter.Neo4jAdapter'] },
      { node_id: 'cig.api.routes.graph.get_node_impact', distance: 2, path: [nodeId, 'cig.storage.neo4j_adapter.Neo4jAdapter', 'cig.api.routes.graph.get_node_impact'] }
    ];
    return {
      data: {
        root_node_id: nodeId,
        max_hops: maxHops,
        total_downstream: mockImpact.length,
        downstream_nodes: mockImpact
      },
      isMock: true
    };
  }
}

export async function searchCodebase(query, topK = 5, intentFilter = null, smellFilter = null) {
  try {
    const payload = {
      query,
      top_k: topK,
      intent_filter: intentFilter || undefined,
      smell_filter: smellFilter || undefined
    };

    const response = await fetch(`${BASE_URL}/search`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', 'Accept': 'application/json' },
      body: JSON.stringify(payload)
    });

    if (!response.ok) throw new Error(`HTTP ${response.status}`);
    const data = await response.json();
    return { data, isMock: false };
  } catch (err) {
    console.warn('Backend API search failed, using client-side mock search:', err.message);
    const lowerQ = query.toLowerCase();
    const results = MOCK_NODES
      .map(node => {
        let score = 0.3;
        if (node.name.toLowerCase().includes(lowerQ)) score += 0.5;
        if (node.docstring && node.docstring.toLowerCase().includes(lowerQ)) score += 0.3;
        if (node.annotations?.summary && node.annotations.summary.toLowerCase().includes(lowerQ)) score += 0.3;
        if (intentFilter && node.annotations?.intent_labels?.includes(intentFilter)) score += 0.2;
        if (smellFilter && node.annotations?.smell_labels?.includes(smellFilter)) score += 0.2;
        return { node_id: node.id, score: Math.min(0.99, score), node };
      })
      .filter(r => r.score > 0.35)
      .sort((a, b) => b.score - a.score)
      .slice(0, topK);

    return {
      data: {
        query,
        total_results: results.length,
        results
      },
      isMock: true
    };
  }
}
