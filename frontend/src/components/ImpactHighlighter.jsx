import React from 'react';
import { GitBranch, X, AlertTriangle, Layers, ArrowRight } from 'lucide-react';

export default function ImpactHighlighter({ impactData, maxHops, setMaxHops, onClearImpact }) {
  if (!impactData) return null;

  const rootId = impactData.root_node_id || 'Unknown';
  const count = impactData.total_downstream || 0;
  const downstreamList = impactData.downstream_nodes || [];

  return (
    <div className="absolute top-4 right-4 z-20 bg-[#111827]/95 border border-amber-500/50 rounded-xl p-4 shadow-2xl backdrop-blur-md max-w-md text-slate-100 animate-in fade-in slide-in-from-top-4 duration-300">
      <div className="flex items-center justify-between border-b border-amber-500/30 pb-2.5 mb-3">
        <div className="flex items-center space-x-2">
          <div className="p-1.5 bg-amber-500/20 text-amber-400 rounded-lg">
            <GitBranch className="w-5 h-5 animate-pulse" />
          </div>
          <div>
            <h3 className="text-sm font-bold text-amber-400 tracking-wide flex items-center gap-1.5">
              Impact Analysis Mode
            </h3>
            <p className="text-[11px] font-mono text-slate-400 truncate max-w-[240px]">
              Root: <strong className="text-white">{rootId.split('.').pop()}</strong>
            </p>
          </div>
        </div>

        <button
          onClick={onClearImpact}
          className="text-gray-400 hover:text-white p-1 rounded hover:bg-gray-800 transition"
          title="Exit Impact Mode"
        >
          <X className="w-4 h-4" />
        </button>
      </div>

      {/* Downstream Stats & Hops Controls */}
      <div className="space-y-3 text-xs">
        <div className="flex items-center justify-between bg-gray-900/80 p-2.5 rounded-lg border border-gray-800">
          <div className="flex items-center space-x-2">
            <Layers className="w-4 h-4 text-blue-400" />
            <span className="text-slate-300">Max Traversal Hops:</span>
          </div>
          <div className="flex items-center space-x-2 font-mono">
            {[1, 2, 3, 5].map((h) => (
              <button
                key={h}
                onClick={() => setMaxHops(h)}
                className={`px-2 py-0.5 rounded text-xs transition ${
                  maxHops === h
                    ? 'bg-amber-500 text-black font-bold'
                    : 'bg-gray-800 text-slate-300 hover:bg-gray-700'
                }`}
              >
                {h}h
              </button>
            ))}
          </div>
        </div>

        <div className="flex items-center justify-between text-slate-300 px-1 font-mono">
          <span>Downstream Impacted Symbols:</span>
          <span className="text-amber-400 font-bold bg-amber-950/60 border border-amber-800/80 px-2 py-0.5 rounded text-xs">
            {count} Nodes
          </span>
        </div>

        {/* Downstream Nodes Preview */}
        {downstreamList.length > 0 && (
          <div className="max-h-36 overflow-y-auto space-y-1 pr-1 bg-gray-950/60 p-2 rounded-lg border border-gray-800 font-mono text-[11px]">
            {downstreamList.map((item, i) => {
              const nodeName = item.node_id ? item.node_id.split('.').pop() : `Node ${i}`;
              return (
                <div key={i} className="flex items-center justify-between text-slate-300 py-0.5 border-b border-gray-800/40 last:border-0">
                  <div className="flex items-center space-x-1.5">
                    <ArrowRight className="w-3 h-3 text-amber-500" />
                    <span className="text-amber-300 font-semibold">{nodeName}</span>
                  </div>
                  <span className="text-[10px] text-slate-400 bg-gray-900 px-1.5 py-0.2 rounded border border-gray-800">
                    dist: {item.distance} hop{item.distance > 1 ? 's' : ''}
                  </span>
                </div>
              );
            })}
          </div>
        )}

        <div className="text-[10px] text-amber-400/80 bg-amber-950/30 p-2 rounded border border-amber-900/50 flex items-center space-x-1.5">
          <AlertTriangle className="w-3.5 h-3.5 shrink-0" />
          <span>Non-impacted graph nodes are currently dimmed in the visualization canvas.</span>
        </div>
      </div>
    </div>
  );
}
