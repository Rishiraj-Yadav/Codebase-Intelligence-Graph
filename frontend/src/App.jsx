import React, { useState, useEffect, useMemo } from 'react';
import Header from './components/Header';
import SearchBox from './components/SearchBox';
import FilterBar from './components/FilterBar';
import GraphViewer from './components/GraphViewer';
import NodeDrawer from './components/NodeDrawer';
import ImpactHighlighter from './components/ImpactHighlighter';
import { fetchNodes, fetchEdges, fetchImpactAnalysis } from './api/client';

export default function App() {
  const [allNodes, setAllNodes] = useState([]);
  const [allEdges, setAllEdges] = useState([]);
  const [isMock, setIsMock] = useState(false);
  const [loading, setLoading] = useState(true);

  // Selection & Inspector State
  const [selectedNode, setSelectedNode] = useState(null);
  const [impactData, setImpactData] = useState(null);
  const [maxHops, setMaxHops] = useState(3);

  // Composable Filters State
  const [filters, setFilters] = useState({
    intents: [],
    minDocScore: 0,
    smell: '',
    filePath: '',
    nodeType: ''
  });

  // Initial Data Fetching with automated fallback
  useEffect(() => {
    async function loadGraphData() {
      setLoading(true);
      const [nodesRes, edgesRes] = await Promise.all([
        fetchNodes(),
        fetchEdges()
      ]);

      setAllNodes(nodesRes.data || []);
      setAllEdges(edgesRes.data || []);
      setIsMock(nodesRes.isMock || edgesRes.isMock);
      setLoading(false);
    }

    loadGraphData();
  }, []);

  // Filtered Nodes Calculation
  const filteredNodes = useMemo(() => {
    return allNodes.filter(node => {
      // 1. Node Type Filter
      if (filters.nodeType && node.node_type !== filters.nodeType) {
        return false;
      }

      // 2. Intent Multi-Select Filter (Matches if node contains ANY selected intent)
      if (filters.intents.length > 0) {
        const nodeIntents = node.annotations?.intent_labels || [];
        const hasMatch = filters.intents.some(i => nodeIntents.includes(i));
        if (!hasMatch) return false;
      }

      // 3. Min Doc Quality Score Filter (0-100)
      if (filters.minDocScore > 0) {
        const rawScore = node.annotations?.doc_quality_score;
        const score = rawScore !== undefined && rawScore !== null
          ? (rawScore <= 1.0 ? Math.round(rawScore * 100) : Math.round(rawScore))
          : 70;
        if (score < filters.minDocScore) return false;
      }

      // 4. Code Smell Filter
      if (filters.smell) {
        const nodeSmells = node.annotations?.smell_labels || [];
        if (filters.smell === 'any') {
          if (nodeSmells.length === 0) return false;
        } else {
          if (!nodeSmells.includes(filters.smell)) return false;
        }
      }

      // 5. File Path Filter
      if (filters.filePath) {
        const pathLower = filters.filePath.toLowerCase();
        const nodePath = (node.file_path || '').toLowerCase();
        if (!nodePath.includes(pathLower)) return false;
      }

      return true;
    });
  }, [allNodes, filters]);

  // Connected Edges for Selected Node
  const connectedEdges = useMemo(() => {
    if (!selectedNode) return [];
    const id = selectedNode.id;
    return allEdges.filter(e => {
      const src = typeof e.source === 'object' ? e.source.id : (e.source || e.source_id);
      const tgt = typeof e.target === 'object' ? e.target.id : (e.target || e.target_id);
      return src === id || tgt === id;
    });
  }, [allEdges, selectedNode]);

  // Trigger Impact Analysis for a Root Node
  const handleTriggerImpact = async (nodeId, hops = maxHops) => {
    const res = await fetchImpactAnalysis(nodeId, hops);
    if (res.data) {
      setImpactData(res.data);
    }
  };

  // Re-fetch Impact Analysis when maxHops changes
  useEffect(() => {
    if (impactData?.root_node_id) {
      handleTriggerImpact(impactData.root_node_id, maxHops);
    }
  }, [maxHops]);

  const handleResetFilters = () => {
    setFilters({
      intents: [],
      minDocScore: 0,
      smell: '',
      filePath: '',
      nodeType: ''
    });
    setSelectedNode(null);
    setImpactData(null);
  };

  return (
    <div className="flex flex-col h-screen w-screen overflow-hidden bg-[#0B0F17] text-slate-100 font-sans selection:bg-blue-600 selection:text-white">
      {/* Header Bar */}
      <Header
        isMock={isMock}
        totalNodes={allNodes.length}
        totalEdges={allEdges.length}
        filteredCount={filteredNodes.length}
        onResetFilters={handleResetFilters}
      />

      {/* Main Content Workspace */}
      <div className="flex flex-1 relative overflow-hidden">
        {/* Left Filter Side Panel */}
        <FilterBar
          filters={filters}
          setFilters={setFilters}
          onClearFilters={handleResetFilters}
        />

        {/* Central Visualization Canvas */}
        <main className="flex-1 relative flex flex-col h-full bg-[#0B0F17]">
          {/* Natural Language Search Overlay */}
          <div className="p-4 z-20 pointer-events-auto">
            <SearchBox
              onSelectNode={(node) => setSelectedNode(node)}
              activeIntentFilter={filters.intents[0]}
              activeSmellFilter={filters.smell}
            />
          </div>

          {/* Impact Analysis Mode Controller */}
          <ImpactHighlighter
            impactData={impactData}
            maxHops={maxHops}
            setMaxHops={setMaxHops}
            onClearImpact={() => setImpactData(null)}
          />

          {/* D3 Graph Viewport */}
          <div className="flex-1 w-full h-full relative" onClick={() => setSelectedNode(null)}>
            {loading ? (
              <div className="absolute inset-0 flex items-center justify-center bg-[#0B0F17]/80 z-20">
                <div className="flex flex-col items-center space-y-3">
                  <div className="w-10 h-10 border-4 border-blue-500 border-t-transparent rounded-full animate-spin" />
                  <span className="text-sm font-mono text-slate-300">Loading Codebase Graph...</span>
                </div>
              </div>
            ) : (
              <GraphViewer
                nodes={filteredNodes}
                edges={allEdges}
                selectedNode={selectedNode}
                onSelectNode={(node) => setSelectedNode(node)}
                impactData={impactData}
                filters={filters}
              />
            )}
          </div>
        </main>

        {/* Right Slide-over Inspector Drawer */}
        {selectedNode && (
          <NodeDrawer
            node={selectedNode}
            connectedEdges={connectedEdges}
            onClose={() => setSelectedNode(null)}
            onTriggerImpact={handleTriggerImpact}
          />
        )}
      </div>
    </div>
  );
}
