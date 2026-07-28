import React, { useState } from 'react';
import { Search, X, Sparkles, ChevronRight, FileCode, CheckCircle2 } from 'lucide-react';
import { searchCodebase } from '../api/client';

export default function SearchBox({ onSelectNode, activeIntentFilter, activeSmellFilter }) {
  const [query, setQuery] = useState('');
  const [topK, setTopK] = useState(5);
  const [isSearching, setIsSearching] = useState(false);
  const [results, setResults] = useState(null);
  const [isOpen, setIsOpen] = useState(false);

  const handleSearch = async (e) => {
    e?.preventDefault();
    if (!query.trim()) return;

    setIsSearching(true);
    setIsOpen(true);
    const searchRes = await searchCodebase(query.trim(), topK, activeIntentFilter, activeSmellFilter);
    setIsSearching(false);

    if (searchRes.data?.results) {
      setResults(searchRes.data.results);
    } else {
      setResults([]);
    }
  };

  const handleClear = () => {
    setQuery('');
    setResults(null);
    setIsOpen(false);
  };

  const handleSelectResult = (node) => {
    onSelectNode(node);
    setIsOpen(false);
  };

  return (
    <div className="relative z-30 w-full max-w-2xl mx-auto">
      <form onSubmit={handleSearch} className="relative flex items-center">
        <div className="absolute left-3.5 text-gray-400 flex items-center pointer-events-none">
          <Search className="w-4 h-4 text-blue-400" />
        </div>
        <input
          type="text"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          onFocus={() => results && setIsOpen(true)}
          placeholder="Natural language semantic search (e.g. 'verify user authorization JWT tokens' or 'database queries')..."
          className="w-full bg-[#1F2937]/90 text-sm text-slate-100 placeholder-slate-400 pl-10 pr-28 py-2.5 rounded-lg border border-gray-700 focus:outline-none focus:border-blue-500 focus:ring-1 focus:ring-blue-500 transition shadow-inner font-sans"
        />

        {query && (
          <button
            type="button"
            onClick={handleClear}
            className="absolute right-24 text-gray-400 hover:text-slate-200 p-1"
          >
            <X className="w-4 h-4" />
          </button>
        )}

        {/* Top-K Selector & Search Button */}
        <div className="absolute right-1.5 flex items-center space-x-1">
          <select
            value={topK}
            onChange={(e) => setTopK(Number(e.target.value))}
            className="bg-gray-800 text-xs text-slate-300 border border-gray-700 rounded px-1.5 py-1 focus:outline-none focus:border-blue-500"
            title="Top K results"
          >
            <option value={3}>k=3</option>
            <option value={5}>k=5</option>
            <option value={10}>k=10</option>
          </select>
          <button
            type="submit"
            disabled={isSearching}
            className="bg-blue-600 hover:bg-blue-500 text-white text-xs font-semibold px-3 py-1.5 rounded flex items-center space-x-1 transition shadow disabled:opacity-50"
          >
            {isSearching ? (
              <span className="animate-pulse">Searching...</span>
            ) : (
              <>
                <Sparkles className="w-3.5 h-3.5 text-blue-200" />
                <span>Search</span>
              </>
            )}
          </button>
        </div>
      </form>

      {/* Floating Results Panel */}
      {isOpen && results && (
        <div className="absolute top-full left-0 right-0 mt-2 bg-[#111827] border border-gray-700 rounded-lg shadow-2xl overflow-hidden z-40 max-h-96 overflow-y-auto">
          <div className="px-4 py-2.5 bg-gray-900 border-b border-gray-800 flex items-center justify-between">
            <span className="text-xs font-semibold text-slate-300 flex items-center gap-1.5">
              <Sparkles className="w-3.5 h-3.5 text-blue-400" />
              UniXcoder Semantic Search Results ({results.length})
            </span>
            <button
              onClick={() => setIsOpen(false)}
              className="text-xs text-gray-400 hover:text-slate-200"
            >
              Close
            </button>
          </div>

          {results.length === 0 ? (
            <div className="p-6 text-center text-sm text-slate-400">
              No matching codebase symbols found for "{query}".
            </div>
          ) : (
            <div className="divide-y divide-gray-800">
              {results.map((res, idx) => {
                const node = res.node || {};
                const scorePct = (res.score * 100).toFixed(1);
                return (
                  <div
                    key={res.node_id || idx}
                    onClick={() => handleSelectResult(node)}
                    className="p-3 hover:bg-gray-800/80 cursor-pointer transition flex items-start justify-between group"
                  >
                    <div className="space-y-1 flex-1 pr-3">
                      <div className="flex items-center space-x-2">
                        <FileCode className="w-4 h-4 text-blue-400 shrink-0" />
                        <span className="text-sm font-mono font-semibold text-white group-hover:text-blue-400 transition">
                          {node.name || res.node_id}
                        </span>
                        <span className="text-xs font-mono px-1.5 py-0.5 rounded bg-gray-800 text-slate-400 border border-gray-700">
                          {node.node_type || 'symbol'}
                        </span>
                      </div>
                      <p className="text-xs text-slate-300 line-clamp-1">
                        {node.annotations?.summary || node.docstring || 'No description available'}
                      </p>
                      <div className="flex items-center space-x-2 text-[11px] text-slate-400 font-mono">
                        <span>{node.file_path}</span>
                        {node.annotations?.intent_labels?.length > 0 && (
                          <span className="bg-blue-950 text-blue-300 px-1.5 py-0.2 rounded border border-blue-800">
                            {node.annotations.intent_labels[0]}
                          </span>
                        )}
                      </div>
                    </div>

                    {/* Relevance Score Badge */}
                    <div className="flex flex-col items-end shrink-0">
                      <div className="flex items-center space-x-1 bg-emerald-950 text-emerald-300 border border-emerald-800 px-2 py-0.5 rounded text-xs font-mono font-bold">
                        <CheckCircle2 className="w-3 h-3 text-emerald-400" />
                        <span>{scorePct}%</span>
                      </div>
                      <span className="text-[10px] text-slate-500 mt-1">relevance score</span>
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </div>
      )}
    </div>
  );
}
