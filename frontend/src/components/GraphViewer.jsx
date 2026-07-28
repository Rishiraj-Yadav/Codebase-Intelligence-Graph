import React, { useEffect, useRef, useState } from 'react';
import * as d3 from 'd3';
import { INTENT_COLORS } from '../mockData';
import { ZoomIn, ZoomOut, Maximize2, Sparkles, AlertTriangle, Layers } from 'lucide-react';

export default function GraphViewer({
  nodes,
  edges,
  selectedNode,
  onSelectNode,
  impactData,
  filters
}) {
  const svgRef = useRef(null);
  const wrapperRef = useRef(null);
  const [tooltip, setTooltip] = useState(null);
  const simulationRef = useRef(null);

  // Compute set of downstream node IDs when impactData is active
  const impactNodeIds = React.useMemo(() => {
    if (!impactData) return null;
    const set = new Set();
    set.add(impactData.root_node_id);
    if (impactData.downstream_nodes) {
      impactData.downstream_nodes.forEach(d => set.add(d.node_id));
    }
    return set;
  }, [impactData]);

  useEffect(() => {
    if (!svgRef.current || !wrapperRef.current) return;

    const width = wrapperRef.current.clientWidth || 900;
    const height = wrapperRef.current.clientHeight || 600;

    // Clear previous SVG contents
    d3.select(svgRef.current).selectAll('*').remove();

    const svg = d3.select(svgRef.current)
      .attr('width', width)
      .attr('height', height)
      .attr('viewBox', [0, 0, width, height]);

    // Add marker definitions for directed edges
    const defs = svg.append('defs');
    
    // Normal arrow
    defs.append('marker')
      .attr('id', 'arrow-normal')
      .attr('viewBox', '0 -5 10 10')
      .attr('refX', 22)
      .attr('refY', 0)
      .attr('markerWidth', 6)
      .attr('markerHeight', 6)
      .attr('orient', 'auto')
      .append('path')
      .attr('d', 'M0,-5L10,0L0,5')
      .attr('fill', '#4B5563');

    // Impact arrow
    defs.append('marker')
      .attr('id', 'arrow-impact')
      .attr('viewBox', '0 -5 10 10')
      .attr('refX', 24)
      .attr('refY', 0)
      .attr('markerWidth', 7)
      .attr('markerHeight', 7)
      .attr('orient', 'auto')
      .append('path')
      .attr('d', 'M0,-5L10,0L0,5')
      .attr('fill', '#F59E0B');

    const container = svg.append('g').attr('class', 'graph-container');

    // Configure D3 Zooming
    const zoom = d3.zoom()
      .scaleExtent([0.2, 4])
      .on('zoom', (event) => {
        container.attr('transform', event.transform);
      });

    svg.call(zoom);

    // Prepare deep clones of graph nodes and links for simulation
    const nodesMap = new Map();
    const graphNodes = nodes.map(n => {
      const copy = { ...n };
      nodesMap.set(n.id, copy);
      return copy;
    });

    const graphEdges = edges
      .filter(e => {
        const srcId = typeof e.source === 'object' ? e.source.id : (e.source || e.source_id);
        const tgtId = typeof e.target === 'object' ? e.target.id : (e.target || e.target_id);
        return nodesMap.has(srcId) && nodesMap.has(tgtId);
      })
      .map(e => ({
        ...e,
        source: typeof e.source === 'object' ? e.source.id : (e.source || e.source_id),
        target: typeof e.target === 'object' ? e.target.id : (e.target || e.target_id)
      }));

    // Setup Force Simulation
    const simulation = d3.forceSimulation(graphNodes)
      .force('link', d3.forceLink(graphEdges).id(d => d.id).distance(130))
      .force('charge', d3.forceManyBody().strength(-400))
      .force('center', d3.forceCenter(width / 2, height / 2))
      .force('collide', d3.forceCollide().radius(d => getNodeRadius(d) + 15));

    simulationRef.current = simulation;

    // Draw Links/Edges
    const link = container.append('g')
      .attr('class', 'links')
      .selectAll('g')
      .data(graphEdges)
      .enter()
      .append('g')
      .attr('class', 'edge-group');

    const linkPath = link.append('path')
      .attr('class', 'graph-link')
      .attr('stroke', d => {
        if (impactNodeIds) {
          const srcId = typeof d.source === 'object' ? d.source.id : d.source;
          const tgtId = typeof d.target === 'object' ? d.target.id : d.target;
          if (impactNodeIds.has(srcId) && impactNodeIds.has(tgtId)) return '#F59E0B';
          return '#1F2937';
        }
        return '#374151';
      })
      .attr('stroke-width', d => (impactNodeIds && isImpactLink(d, impactNodeIds) ? 2.5 : 1.5))
      .attr('stroke-dasharray', d => d.edge_type === 'imports' ? '4 4' : 'none')
      .attr('marker-end', d => impactNodeIds && isImpactLink(d, impactNodeIds) ? 'url(#arrow-impact)' : 'url(#arrow-normal)');

    // Optional Edge Labels
    const linkText = link.append('text')
      .attr('font-size', '9px')
      .attr('fill', '#9CA3AF')
      .attr('font-family', 'monospace')
      .attr('text-anchor', 'middle')
      .text(d => d.annotations?.label || d.edge_type || '');

    // Draw Nodes
    const node = container.append('g')
      .attr('class', 'nodes')
      .selectAll('g')
      .data(graphNodes)
      .enter()
      .append('g')
      .attr('class', 'graph-node')
      .style('opacity', d => {
        if (!impactNodeIds) return 1.0;
        return impactNodeIds.has(d.id) ? 1.0 : 0.15;
      })
      .call(d3.drag()
        .on('start', (event, d) => {
          if (!event.active) simulation.alphaTarget(0.3).restart();
          d.fx = d.x;
          d.fy = d.y;
        })
        .on('drag', (event, d) => {
          d.fx = event.x;
          d.fy = event.y;
        })
        .on('end', (event, d) => {
          if (!event.active) simulation.alphaTarget(0);
          d.fx = null;
          d.fy = null;
        })
      );

    // Node Base Circle
    node.append('circle')
      .attr('r', d => getNodeRadius(d))
      .attr('fill', d => getNodeFillColor(d))
      .attr('stroke', d => getNodeStrokeColor(d))
      .attr('stroke-width', d => {
        if (selectedNode && selectedNode.id === d.id) return '4px';
        return getNodeStrokeWidth(d);
      })
      .attr('class', d => {
        const smells = d.annotations?.smell_labels || [];
        const isImpactRoot = impactData && impactData.root_node_id === d.id;
        if (isImpactRoot) return 'node-impact-highlight';
        if (smells.length > 0) return 'node-smell-pulse';
        return '';
      });

    // Node Type Icon / Inner Indicator
    node.append('text')
      .attr('text-anchor', 'middle')
      .attr('dy', '0.35em')
      .attr('fill', '#FFFFFF')
      .attr('font-size', '10px')
      .attr('font-weight', 'bold')
      .text(d => (d.node_type === 'class' ? 'C' : d.node_type === 'module' ? 'M' : 'ƒ'));

    // Node Label under circle
    node.append('text')
      .attr('text-anchor', 'middle')
      .attr('dy', d => getNodeRadius(d) + 14)
      .attr('fill', d => (selectedNode && selectedNode.id === d.id ? '#60A5FA' : '#E2E8F0'))
      .attr('font-weight', d => (selectedNode && selectedNode.id === d.id ? '700' : '500'))
      .text(d => d.name || d.id.split('.').pop());

    // Node Hover & Click Handlers
    node
      .on('mouseover', (event, d) => {
        setTooltip({
          x: event.clientX,
          y: event.clientY,
          node: d
        });
      })
      .on('mousemove', (event) => {
        setTooltip(prev => prev ? { ...prev, x: event.clientX, y: event.clientY } : null);
      })
      .on('mouseout', () => {
        setTooltip(null);
      })
      .on('click', (event, d) => {
        event.stopPropagation();
        onSelectNode(d);
      });

    // Simulation Tick Listener
    simulation.on('tick', () => {
      linkPath.attr('d', d => {
        const dx = d.target.x - d.source.x;
        const dy = d.target.y - d.source.y;
        return `M${d.source.x},${d.source.y}L${d.target.x},${d.target.y}`;
      });

      linkText
        .attr('x', d => (d.source.x + d.target.x) / 2)
        .attr('y', d => (d.source.y + d.target.y) / 2 - 4);

      node.attr('transform', d => `translate(${d.x},${d.y})`);
    });

    return () => {
      simulation.stop();
    };
  }, [nodes, edges, selectedNode, impactData, impactNodeIds]);

  const handleZoomIn = () => {
    if (!svgRef.current) return;
    d3.select(svgRef.current).transition().duration(300).call(d3.zoom().scaleBy, 1.3);
  };

  const handleZoomOut = () => {
    if (!svgRef.current) return;
    d3.select(svgRef.current).transition().duration(300).call(d3.zoom().scaleBy, 0.7);
  };

  const handleResetZoom = () => {
    if (!svgRef.current) return;
    d3.select(svgRef.current).transition().duration(400).call(
      d3.zoom().transform,
      d3.zoomIdentity
    );
  };

  return (
    <div ref={wrapperRef} className="relative w-full h-full bg-[#0B0F17] overflow-hidden select-none">
      <svg ref={svgRef} className="graph-svg w-full h-full" />

      {/* Floating Canvas Controls */}
      <div className="absolute bottom-6 left-6 flex items-center space-x-1.5 bg-[#111827]/90 border border-gray-800 p-1.5 rounded-lg shadow-xl backdrop-blur-md z-10">
        <button
          onClick={handleZoomIn}
          className="p-1.5 text-slate-300 hover:text-white hover:bg-gray-800 rounded transition"
          title="Zoom In"
        >
          <ZoomIn className="w-4 h-4" />
        </button>
        <button
          onClick={handleZoomOut}
          className="p-1.5 text-slate-300 hover:text-white hover:bg-gray-800 rounded transition"
          title="Zoom Out"
        >
          <ZoomOut className="w-4 h-4" />
        </button>
        <div className="w-px h-4 bg-gray-800" />
        <button
          onClick={handleResetZoom}
          className="p-1.5 text-slate-300 hover:text-white hover:bg-gray-800 rounded transition"
          title="Reset Zoom & Pan"
        >
          <Maximize2 className="w-4 h-4" />
        </button>
      </div>

      {/* Hover Tooltip Overlay */}
      {tooltip && tooltip.node && (
        <div
          className="fixed z-50 pointer-events-none bg-[#111827]/95 border border-gray-700 rounded-lg p-3 shadow-2xl backdrop-blur-md text-xs space-y-1.5 max-w-xs font-sans transform -translate-x-1/2 -translate-y-full -mt-3"
          style={{ left: `${tooltip.x}px`, top: `${tooltip.y}px` }}
        >
          <div className="flex items-center justify-between border-b border-gray-800 pb-1">
            <span className="font-mono font-bold text-white text-sm">{tooltip.node.name}</span>
            <span className="font-mono text-[10px] bg-blue-950 text-blue-300 border border-blue-800 px-1.5 py-0.2 rounded capitalize">
              {tooltip.node.node_type}
            </span>
          </div>

          <p className="text-slate-300 text-[11px] line-clamp-2">
            {tooltip.node.annotations?.summary || tooltip.node.docstring || 'No summary generated yet.'}
          </p>

          <div className="pt-1 flex flex-wrap gap-1 items-center text-[10px] font-mono">
            {/* Primary Intent Badge */}
            {tooltip.node.annotations?.intent_labels?.[0] && (
              <span
                className="px-1.5 py-0.5 rounded text-white font-semibold"
                style={{ backgroundColor: INTENT_COLORS[tooltip.node.annotations.intent_labels[0]] || '#3B82F6' }}
              >
                {tooltip.node.annotations.intent_labels[0]}
              </span>
            )}

            {/* Doc Quality Score Badge */}
            <span className="px-1.5 py-0.5 rounded bg-gray-800 text-emerald-400 border border-gray-700">
              Doc Score: {getDocScore(tooltip.node)}/100
            </span>

            {/* Code Smell Warning Badge */}
            {tooltip.node.annotations?.smell_labels?.length > 0 && (
              <span className="px-1.5 py-0.5 rounded bg-red-950 text-red-300 border border-red-800 flex items-center gap-1 font-bold">
                <AlertTriangle className="w-3 h-3" />
                {tooltip.node.annotations.smell_labels.length} Smell(s)
              </span>
            )}
          </div>
        </div>
      )}
    </div>
  );
}

// Helper Functions for Dynamic Visual Encoding
function getNodeRadius(node) {
  const span = node.source_span;
  let lines = 15;
  if (span && span.start_line && span.end_line) {
    lines = Math.max(1, span.end_line - span.start_line + 1);
  }
  return Math.max(14, Math.min(30, 10 + Math.sqrt(lines) * 2.5));
}

function getNodeFillColor(node) {
  const primaryIntent = node.annotations?.intent_labels?.[0];
  if (primaryIntent && INTENT_COLORS[primaryIntent]) {
    return INTENT_COLORS[primaryIntent];
  }
  return '#3B82F6';
}

function getDocScore(node) {
  const rawScore = node.annotations?.doc_quality_score;
  if (rawScore === undefined || rawScore === null) return 70;
  return rawScore <= 1.0 ? Math.round(rawScore * 100) : Math.round(rawScore);
}

function getNodeStrokeColor(node) {
  const score = getDocScore(node);
  if (score >= 80) return '#10B981'; // Green (high quality docs)
  if (score >= 50) return '#F59E0B'; // Amber (medium quality docs)
  return '#EF4444'; // Red (poor/missing docs)
}

function getNodeStrokeWidth(node) {
  const score = getDocScore(node);
  if (score < 50) return '3.5px';
  return '2.5px';
}

function isImpactLink(edge, impactSet) {
  const src = typeof edge.source === 'object' ? edge.source.id : edge.source;
  const tgt = typeof edge.target === 'object' ? edge.target.id : edge.target;
  return impactSet.has(src) && impactSet.has(tgt);
}
