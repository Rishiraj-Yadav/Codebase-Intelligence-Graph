import React, { useState } from 'react';
import {
  X,
  FileCode,
  Sparkles,
  Award,
  Tag,
  AlertTriangle,
  GitCommit,
  GitBranch,
  CheckCircle2,
  HelpCircle,
  Code2,
  Layers,
  ArrowRight
} from 'lucide-react';
import { INTENT_TAXONOMY, SMELL_TAXONOMY, INTENT_COLORS } from '../mockData';

export default function NodeDrawer({
  node,
  connectedEdges = [],
  onClose,
  onTriggerImpact
}) {
  if (!node) return null;

  const annotations = node.annotations || {};
  const span = node.source_span || {};
  const docScore = getDocScore(node);
  const docConfidence = annotations.doc_score_confidence ?? 0.90;
  const summaryConfidence = annotations.summary_confidence ?? 0.92;
  const intentConfidence = annotations.intent_confidence ?? 0.94;
  const smellConfidence = annotations.smell_confidence ?? 0.91;

  const activeIntents = annotations.intent_labels || [];
  const activeSmells = annotations.smell_labels || [];
  const smellProbs = annotations.smell_probabilities || {};

  return (
    <aside className="fixed top-0 right-0 bottom-0 w-[520px] bg-[#111827] border-l border-gray-800 shadow-2xl z-40 flex flex-col h-full animate-in slide-in-from-right duration-300">
      {/* Header */}
      <div className="p-5 border-b border-gray-800 bg-gray-900/80 flex items-start justify-between shrink-0">
        <div className="space-y-1 pr-4">
          <div className="flex items-center space-x-2">
            <FileCode className="w-5 h-5 text-blue-400 shrink-0" />
            <h2 className="text-lg font-mono font-bold text-white truncate max-w-[360px]" title={node.name}>
              {node.name || node.id}
            </h2>
            <span className="text-xs font-mono px-2 py-0.5 rounded bg-gray-800 text-blue-300 border border-gray-700 capitalize shrink-0">
              {node.node_type || 'symbol'}
            </span>
          </div>
          <div className="text-xs font-mono text-slate-400 flex items-center space-x-2 truncate">
            <span>{node.file_path}</span>
            {span.start_line && (
              <span className="text-slate-500">
                (L{span.start_line}-L{span.end_line})
              </span>
            )}
          </div>
        </div>

        <button
          onClick={onClose}
          className="text-gray-400 hover:text-white p-1 rounded-lg hover:bg-gray-800 transition shrink-0"
          title="Close Inspector"
        >
          <X className="w-5 h-5" />
        </button>
      </div>

      {/* Main Drawer Body */}
      <div className="p-5 space-y-6 overflow-y-auto flex-1 font-sans">
        {/* Primary Impact Analysis Action */}
        <button
          onClick={() => onTriggerImpact(node.id)}
          className="w-full bg-gradient-to-r from-amber-600 to-red-600 hover:from-amber-500 hover:to-red-500 text-white font-semibold py-2.5 px-4 rounded-lg shadow-lg flex items-center justify-center space-x-2 transition transform active:scale-95"
        >
          <GitBranch className="w-4 h-4" />
          <span>Show Impact Analysis (Downstream Reachability)</span>
        </button>

        {/* M1: CodeT5 Summary Card */}
        <section className="bg-gray-900/60 border border-gray-800 rounded-xl p-4 space-y-2">
          <div className="flex items-center justify-between">
            <h3 className="text-xs font-bold text-blue-400 tracking-wider uppercase flex items-center gap-1.5">
              <Sparkles className="w-4 h-4 text-blue-400" />
              M1 CodeT5 Natural Language Summary
            </h3>
            <span className="text-[11px] font-mono text-slate-400 bg-gray-800 px-2 py-0.5 rounded border border-gray-700">
              Conf: <strong className="text-blue-300">{(summaryConfidence * 100).toFixed(0)}%</strong>
            </span>
          </div>
          <p className="text-sm text-slate-200 leading-relaxed font-sans bg-gray-950/60 p-3 rounded-lg border border-gray-800">
            {annotations.summary || node.docstring || 'No summary generated for this node.'}
          </p>
        </section>

        {/* M2: CodeBERT Doc Quality Score */}
        <section className="bg-gray-900/60 border border-gray-800 rounded-xl p-4 space-y-3">
          <div className="flex items-center justify-between">
            <h3 className="text-xs font-bold text-emerald-400 tracking-wider uppercase flex items-center gap-1.5">
              <Award className="w-4 h-4 text-emerald-400" />
              M2 CodeBERT Documentation Quality Score
            </h3>
            <span className="text-[11px] font-mono text-slate-400 bg-gray-800 px-2 py-0.5 rounded border border-gray-700">
              Conf: <strong className="text-emerald-300">{(docConfidence * 100).toFixed(0)}%</strong>
            </span>
          </div>

          <div className="flex items-center space-x-4">
            <div className="flex flex-col items-center justify-center w-20 h-20 rounded-full border-4 border-gray-800 bg-gray-950 shrink-0"
                 style={{
                   borderColor: docScore >= 80 ? '#10B981' : docScore >= 50 ? '#F59E0B' : '#EF4444'
                 }}
            >
              <span className="text-xl font-bold font-mono text-white">{docScore}</span>
              <span className="text-[10px] text-slate-400 font-mono">out of 100</span>
            </div>

            <div className="space-y-1.5 flex-1 text-xs">
              <div className="font-semibold text-slate-200">
                {docScore >= 80 ? 'High Quality Documentation' : docScore >= 50 ? 'Moderate Documentation Quality' : 'Needs Documentation Improvement'}
              </div>
              <p className="text-slate-400 text-[11px]">
                {annotations.doc_feedback || 'Docstring clarity and completeness evaluated against CodeBERT benchmarks.'}
              </p>
            </div>
          </div>
        </section>

        {/* M3: Intent Labels & Probability Badges */}
        <section className="bg-gray-900/60 border border-gray-800 rounded-xl p-4 space-y-3">
          <div className="flex items-center justify-between">
            <h3 className="text-xs font-bold text-indigo-400 tracking-wider uppercase flex items-center gap-1.5">
              <Tag className="w-4 h-4 text-indigo-400" />
              M3 Intent Taxonomy Labels (15 Categories)
            </h3>
            <span className="text-[11px] font-mono text-slate-400 bg-gray-800 px-2 py-0.5 rounded border border-gray-700">
              Conf: <strong className="text-indigo-300">{(intentConfidence * 100).toFixed(0)}%</strong>
            </span>
          </div>

          <div className="flex flex-wrap gap-1.5">
            {INTENT_TAXONOMY.map(cat => {
              const isActive = activeIntents.includes(cat);
              const catColor = INTENT_COLORS[cat] || '#3B82F6';
              return (
                <span
                  key={cat}
                  className={`text-xs px-2.5 py-1 rounded-md font-mono flex items-center space-x-1.5 transition border ${
                    isActive
                      ? 'text-white font-bold border-transparent shadow'
                      : 'bg-gray-950/40 text-slate-500 border-gray-800 opacity-60'
                  }`}
                  style={{ backgroundColor: isActive ? catColor : undefined }}
                >
                  <span className="w-2 h-2 rounded-full bg-white/80" />
                  <span className="capitalize">{cat}</span>
                </span>
              );
            })}
          </div>
        </section>

        {/* M4: Code Smell Probabilities Breakdown */}
        <section className="bg-gray-900/60 border border-gray-800 rounded-xl p-4 space-y-3">
          <div className="flex items-center justify-between">
            <h3 className="text-xs font-bold text-red-400 tracking-wider uppercase flex items-center gap-1.5">
              <AlertTriangle className="w-4 h-4 text-red-400" />
              M4 GraphCodeBERT Code Smell Probabilities
            </h3>
            <span className="text-[11px] font-mono text-slate-400 bg-gray-800 px-2 py-0.5 rounded border border-gray-700">
              Conf: <strong className="text-red-300">{(smellConfidence * 100).toFixed(0)}%</strong>
            </span>
          </div>

          <div className="space-y-2 text-xs font-mono">
            {SMELL_TAXONOMY.map(smell => {
              const prob = smellProbs[smell] ?? (activeSmells.includes(smell) ? 0.85 : 0.05);
              const probPct = Math.round(prob * 100);
              const isDetected = prob >= 0.5;

              return (
                <div key={smell} className="space-y-1">
                  <div className="flex items-center justify-between text-[11px]">
                    <span className={`capitalize flex items-center gap-1.5 ${isDetected ? 'text-red-400 font-bold' : 'text-slate-400'}`}>
                      {isDetected && <AlertTriangle className="w-3 h-3 text-red-500 shrink-0" />}
                      {smell}
                    </span>
                    <span className={isDetected ? 'text-red-400 font-bold' : 'text-slate-500'}>
                      {probPct}%
                    </span>
                  </div>
                  <div className="w-full h-1.5 bg-gray-800 rounded-full overflow-hidden">
                    <div
                      className={`h-full rounded-full transition-all duration-500 ${
                        isDetected ? 'bg-red-500' : 'bg-slate-700'
                      }`}
                      style={{ width: `${probPct}%` }}
                    />
                  </div>
                </div>
              );
            })}
          </div>
        </section>

        {/* Source Code Snippet Viewer */}
        <section className="bg-gray-900/60 border border-gray-800 rounded-xl p-4 space-y-2">
          <div className="flex items-center justify-between">
            <h3 className="text-xs font-bold text-slate-300 tracking-wider uppercase flex items-center gap-1.5">
              <Code2 className="w-4 h-4 text-blue-400" />
              Source Code Snippet
            </h3>
            <span className="text-[10px] font-mono text-slate-400">
              {node.file_path}
            </span>
          </div>

          <div className="bg-[#0B0F17] rounded-lg p-3 border border-gray-800 font-mono text-xs overflow-x-auto text-slate-200 leading-relaxed max-h-56">
            <pre className="whitespace-pre">
              {node.code_snippet || node.docstring || '// Source code snippet unavailable for this node node'}
            </pre>
          </div>
        </section>

        {/* Connected Edges & M5 Semantic Annotations */}
        <section className="bg-gray-900/60 border border-gray-800 rounded-xl p-4 space-y-3">
          <h3 className="text-xs font-bold text-slate-300 tracking-wider uppercase flex items-center gap-1.5">
            <GitCommit className="w-4 h-4 text-purple-400" />
            Connected Edges & M5 Semantic Edge Labels ({connectedEdges.length})
          </h3>

          {connectedEdges.length === 0 ? (
            <p className="text-xs text-slate-500 italic">No connected edge relationships found.</p>
          ) : (
            <div className="space-y-2 max-h-60 overflow-y-auto pr-1">
              {connectedEdges.map((edge, idx) => {
                const src = typeof edge.source === 'object' ? edge.source.id : (edge.source || edge.source_id);
                const tgt = typeof edge.target === 'object' ? edge.target.id : (edge.target || edge.target_id);
                const isOutgoing = src === node.id;
                const otherId = isOutgoing ? tgt : src;
                const m5 = edge.annotations || {};

                return (
                  <div key={edge.id || idx} className="bg-gray-950 p-2.5 rounded-lg border border-gray-800 space-y-1 text-xs font-mono">
                    <div className="flex items-center justify-between text-slate-300">
                      <div className="flex items-center space-x-1.5 truncate max-w-[280px]">
                        <span className="text-purple-400 font-bold">{isOutgoing ? 'OUT →' : 'IN ←'}</span>
                        <span className="text-white font-semibold truncate">{otherId ? otherId.split('.').pop() : 'Symbol'}</span>
                      </div>
                      <span className="text-[10px] bg-gray-800 px-1.5 py-0.2 rounded text-slate-400 border border-gray-700">
                        {edge.edge_type}
                      </span>
                    </div>

                    {m5.label && (
                      <div className="pt-1 text-[11px] font-sans space-y-0.5 border-t border-gray-900">
                        <div className="flex items-center justify-between text-purple-300 font-medium">
                          <span>M5 Relation: "{m5.label}"</span>
                          <span className="text-[10px] font-mono text-slate-400">
                            Conf: {((m5.confidence || 0.9) * 100).toFixed(0)}%
                          </span>
                        </div>
                        {m5.explanation && (
                          <p className="text-slate-400 text-[10px] leading-snug">{m5.explanation}</p>
                        )}
                      </div>
                    )}
                  </div>
                );
              })}
            </div>
          )}
        </section>
      </div>
    </aside>
  );
}

function getDocScore(node) {
  const raw = node.annotations?.doc_quality_score;
  if (raw === undefined || raw === null) return 70;
  return raw <= 1.0 ? Math.round(raw * 100) : Math.round(raw);
}
