import React from 'react';
import { Network, Database, RefreshCw, Activity, ShieldCheck, Zap } from 'lucide-react';

export default function Header({ isMock, totalNodes, totalEdges, filteredCount, onResetFilters }) {
  return (
    <header className="h-16 bg-[#111827] border-b border-gray-800 px-6 flex items-center justify-between z-20 shadow-lg shrink-0">
      {/* Brand & Logo */}
      <div className="flex items-center space-x-3">
        <div className="p-2 bg-blue-600/20 text-blue-400 rounded-lg border border-blue-500/30 flex items-center justify-center">
          <Network className="w-6 h-6 animate-pulse" />
        </div>
        <div>
          <h1 className="text-lg font-bold tracking-wide text-white flex items-center gap-2">
            Codebase Intelligence Graph <span className="text-xs font-mono font-medium bg-blue-900/60 text-blue-300 border border-blue-700/50 px-2 py-0.5 rounded">CIG v1.0</span>
          </h1>
          <p className="text-xs text-slate-400">AST Graph Exploration & Model Annotations (M1–M5)</p>
        </div>
      </div>

      {/* Stats & Status Badges */}
      <div className="flex items-center space-x-4 text-xs font-mono">
        <div className="flex items-center space-x-3 bg-gray-900/80 px-3 py-1.5 rounded-md border border-gray-800">
          <div className="flex items-center space-x-1.5 text-slate-300">
            <Database className="w-3.5 h-3.5 text-blue-400" />
            <span>Nodes: <strong className="text-white">{filteredCount}</strong> / {totalNodes}</span>
          </div>
          <span className="text-gray-600">|</span>
          <div className="flex items-center space-x-1.5 text-slate-300">
            <Zap className="w-3.5 h-3.5 text-amber-400" />
            <span>Edges: <strong className="text-white">{totalEdges}</strong></span>
          </div>
        </div>

        {/* Connection Mode Indicator */}
        <div className={`flex items-center space-x-1.5 px-3 py-1.5 rounded-md text-xs font-medium border ${
          isMock 
            ? 'bg-amber-950/40 text-amber-300 border-amber-800/60' 
            : 'bg-emerald-950/40 text-emerald-300 border-emerald-800/60'
        }`}>
          <Activity className={`w-3.5 h-3.5 ${isMock ? 'text-amber-400' : 'text-emerald-400 animate-pulse'}`} />
          <span>{isMock ? 'Offline Mock Mode' : 'Connected to API (http://localhost:8000)'}</span>
        </div>

        {/* Reset View */}
        <button
          onClick={onResetFilters}
          className="flex items-center space-x-1.5 bg-gray-800 hover:bg-gray-700 text-slate-200 px-3 py-1.5 rounded-md border border-gray-700 transition"
          title="Reset graph filters & selection"
        >
          <RefreshCw className="w-3.5 h-3.5 text-slate-400" />
          <span>Reset Filters</span>
        </button>
      </div>
    </header>
  );
}
