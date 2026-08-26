"use client";

import React, { useState } from "react";
import { Brain, ChevronDown, ChevronUp, Sparkles } from "lucide-react";

interface ReasoningAccordionProps {
  reasoningText: string;
  durationSeconds?: number;
}

export default function ReasoningAccordion({
  reasoningText,
  durationSeconds = 2.4,
}: ReasoningAccordionProps) {
  const [isExpanded, setIsExpanded] = useState(false);

  if (!reasoningText || !reasoningText.trim()) return null;

  return (
    <div className="mb-3 rounded-2xl border border-indigo-200/60 dark:border-indigo-900/50 bg-indigo-50/40 dark:bg-indigo-950/30 overflow-hidden transition">
      <button
        type="button"
        onClick={() => setIsExpanded(!isExpanded)}
        className="w-full px-4 py-2.5 flex items-center justify-between text-left hover:bg-indigo-100/40 dark:hover:bg-indigo-900/30 transition"
      >
        <div className="flex items-center gap-2">
          <div className="w-5 h-5 rounded-lg bg-indigo-600/20 dark:bg-indigo-500/20 flex items-center justify-center text-indigo-600 dark:text-indigo-400">
            <Brain className="w-3.5 h-3.5" />
          </div>
          <span className="text-xs font-bold text-indigo-900 dark:text-indigo-200">
            Düşünce Süreci (Akıl Yürütme)
          </span>
          <span className="text-[10px] px-2 py-0.5 rounded-full font-mono bg-indigo-200/60 dark:bg-indigo-900 text-indigo-800 dark:text-indigo-300 font-bold">
            ~{durationSeconds.toFixed(1)} sn
          </span>
        </div>

        <div className="text-indigo-600 dark:text-indigo-400">
          {isExpanded ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
        </div>
      </button>

      {isExpanded && (
        <div className="px-4 py-3 border-t border-indigo-200/40 dark:border-indigo-900/40 bg-white/50 dark:bg-gray-950/50 text-xs font-mono text-slate-700 dark:text-gray-300 whitespace-pre-wrap leading-relaxed max-h-64 overflow-y-auto">
          {reasoningText}
        </div>
      )}
    </div>
  );
}
