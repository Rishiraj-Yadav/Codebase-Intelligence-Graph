import React from 'react';
import { Filter, Sliders, AlertTriangle, FileText, Tag, RotateCcw, ChevronDown } from 'lucide-react';
import { INTENT_TAXONOMY, SMELL_TAXONOMY, INTENT_COLORS } from '../mockData';

export default function FilterBar({ filters, setFilters, onClearFilters }) {
  const activeCount = 
    (filters.intents.length > 0 ? 1 : 0) +
    (filters.minDocScore > 0 ? 1 : 0) +
    (filters.smell ? 1 : 0) +
    (filters.filePath ? 1 : 0) +
    (filters.nodeType ? 1 : 0);

  const toggleIntent = (intent) => {
    const exists = filters.intents.includes(intent);
    if (exists) {
      setFilters(prev => ({ ...prev, intents: prev.intents.filter(i => i !== intent) }));
    } else {
      setFilters(prev => ({ ...prev, intents: [...prev.intents, intent] }));
    }
  };

  return (
    <aside className="w-72 bg-[#111827] border-r border-gray-800 flex flex-col h-full z-10 shrink-0 overflow-y-auto">
      {/* Panel Header */}
      <div className="p-4 border-b border-gray-800 flex items-center justify-between bg-gray-900/50">
        <div className="flex items-center space-x-2">
          <Filter className="w-4 h-4 text-blue-400" />
          <h2 className="text-sm font-semibold text-slate-200 uppercase tracking-wider">Graph Filters</h2>
          {activeCount > 0 && (
            <span className="bg-blue-600 text-white text-xs font-mono px-2 py-0.5 rounded-full font-bold">
              {activeCount}
            </span>
          )}
        </div>
        {activeCount > 0 && (
          <button
            onClick={onClearFilters}
            className="text-xs text-slate-400 hover:text-slate-200 flex items-center gap-1 transition"
          >
            <RotateCcw className="w-3 h-3" />
            Reset
          </button>
        )}
      </div>

      <div className="p-4 space-y-6 text-xs">
        {/* Node Type Filter */}
        <div className="space-y-2">
          <label className="text-slate-300 font-medium flex items-center gap-1.5">
            <Tag className="w-3.5 h-3.5 text-blue-400" />
            Node Type
          </label>
          <select
            value={filters.nodeType}
            onChange={(e) => setFilters(prev => ({ ...prev, nodeType: e.target.value }))}
            className="w-full bg-gray-800 border border-gray-700 text-slate-200 rounded p-2 focus:outline-none focus:border-blue-500"
          >
            <option value="">All Symbol Types (Functions, Classes, Modules)</option>
            <option value="function">Function / Method</option>
            <option value="class">Class</option>
            <option value="module">Module / File</option>
          </select>
        </div>

        {/* Intent Categories Multi-Select */}
        <div className="space-y-2.5">
          <div className="flex items-center justify-between">
            <label className="text-slate-300 font-medium flex items-center gap-1.5">
              <Tag className="w-3.5 h-3.5 text-indigo-400" />
              Primary Intent (M3 Taxonomy)
            </label>
            {filters.intents.length > 0 && (
              <button
                onClick={() => setFilters(prev => ({ ...prev, intents: [] }))}
                className="text-[10px] text-blue-400 hover:underline"
              >
                Clear
              </button>
            )}
          </div>
          <div className="max-h-48 overflow-y-auto space-y-1 pr-1 bg-gray-950/40 p-2 rounded border border-gray-800">
            {INTENT_TAXONOMY.map(intent => {
              const checked = filters.intents.includes(intent);
              const color = INTENT_COLORS[intent] || '#3B82F6';
              return (
                <label
                  key={intent}
                  onClick={() => toggleIntent(intent)}
                  className={`flex items-center justify-between px-2 py-1 rounded cursor-pointer transition select-none ${
                    checked ? 'bg-gray-800 text-white font-semibold' : 'hover:bg-gray-900/60 text-slate-300'
                  }`}
                >
                  <div className="flex items-center space-x-2">
                    <span
                      className="w-2.5 h-2.5 rounded-full inline-block shrink-0"
                      style={{ backgroundColor: color }}
                    />
                    <span className="capitalize">{intent}</span>
                  </div>
                  <input
                    type="checkbox"
                    checked={checked}
                    onChange={() => {}}
                    className="rounded border-gray-700 text-blue-600 focus:ring-0 bg-gray-900"
                  />
                </label>
              );
            })}
          </div>
        </div>

        {/* Doc Quality Score Range Slider */}
        <div className="space-y-2">
          <div className="flex items-center justify-between text-slate-300">
            <label className="font-medium flex items-center gap-1.5">
              <Sliders className="w-3.5 h-3.5 text-emerald-400" />
              Min Doc Quality Score (M2)
            </label>
            <span className="font-mono text-emerald-400 font-bold bg-emerald-950/60 border border-emerald-800 px-2 py-0.5 rounded">
              {filters.minDocScore} / 100
            </span>
          </div>
          <input
            type="range"
            min="0"
            max="100"
            step="5"
            value={filters.minDocScore}
            onChange={(e) => setFilters(prev => ({ ...prev, minDocScore: Number(e.target.value) }))}
            className="w-full h-1.5 bg-gray-700 rounded-lg appearance-none cursor-pointer accent-emerald-500"
          />
          <div className="flex justify-between text-[10px] text-slate-500 font-mono">
            <span>0 (Poor Docs)</span>
            <span>50</span>
            <span>100 (Exemplary)</span>
          </div>
        </div>

        {/* Code Smell Filter */}
        <div className="space-y-2">
          <label className="text-slate-300 font-medium flex items-center gap-1.5">
            <AlertTriangle className="w-3.5 h-3.5 text-red-400" />
            Code Smell Filter (M4)
          </label>
          <select
            value={filters.smell}
            onChange={(e) => setFilters(prev => ({ ...prev, smell: e.target.value }))}
            className="w-full bg-gray-800 border border-gray-700 text-slate-200 rounded p-2 focus:outline-none focus:border-blue-500"
          >
            <option value="">All Code Smells (Or Clean)</option>
            <option value="any">Any Smell Detected (&gt; 0)</option>
            {SMELL_TAXONOMY.map(smell => (
              <option key={smell} value={smell}>
                Smell: {smell}
              </option>
            ))}
          </select>
        </div>

        {/* File Path Filter */}
        <div className="space-y-2">
          <label className="text-slate-300 font-medium flex items-center gap-1.5">
            <FileText className="w-3.5 h-3.5 text-amber-400" />
            File Path Filter
          </label>
          <input
            type="text"
            value={filters.filePath}
            onChange={(e) => setFilters(prev => ({ ...prev, filePath: e.target.value }))}
            placeholder="Filter by path (e.g. 'cig/api', 'retrieval')..."
            className="w-full bg-gray-800 border border-gray-700 text-slate-200 rounded p-2 placeholder-slate-500 focus:outline-none focus:border-blue-500 font-mono text-[11px]"
          />
        </div>
      </div>

      {/* Footer Instructions */}
      <div className="mt-auto p-4 border-t border-gray-800 bg-gray-900/40 text-[11px] text-slate-400 space-y-1.5">
        <p className="font-semibold text-slate-300">Graph Visual Legend:</p>
        <div className="flex items-center space-x-2">
          <span className="w-3 h-3 rounded-full border-2 border-red-500 animate-pulse bg-red-950 inline-block" />
          <span>Pulsing Border = Code Smell</span>
        </div>
        <div className="flex items-center space-x-2">
          <span className="w-3 h-3 rounded-full border-2 border-emerald-400 inline-block bg-slate-800" />
          <span>Border Color = M2 Doc Score</span>
        </div>
        <div className="flex items-center space-x-2">
          <span className="w-3 h-3 rounded-full bg-amber-500 inline-block" />
          <span>Node Fill = M3 Primary Intent</span>
        </div>
      </div>
    </aside>
  );
}
