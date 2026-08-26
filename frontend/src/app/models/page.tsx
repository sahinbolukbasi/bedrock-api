"use client";

import React, { useState, useEffect } from "react";
import { Cpu, Search, Sparkles, Check, Image as ImageIcon, Eye, Wrench } from "lucide-react";
import { fetchApi } from "../../lib/api";

export default function ModelsPage() {
  const [models, setModels] = useState<any[]>([]);
  const [search, setSearch] = useState("");
  const [filterType, setFilterType] = useState<string>("ALL");

  useEffect(() => {
    async function loadModels() {
      try {
        const res = await fetchApi("/v1/models");
        if (res.data) setModels(res.data);
      } catch (err) {
        console.error("Failed to load models catalog:", err);
      }
    }
    loadModels();
  }, []);

  const filtered = models.filter((m) => {
    const matchesSearch = m.name.toLowerCase().includes(search.toLowerCase()) || m.id.toLowerCase().includes(search.toLowerCase());
    const matchesType = filterType === "ALL" || m.type === filterType;
    return matchesSearch && matchesType;
  });

  return (
    <div className="max-w-7xl mx-auto px-4 py-8">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-gray-800 pb-6 mb-8">
        <div>
          <h1 className="text-2xl font-bold text-white flex items-center gap-2">
            <Cpu className="w-6 h-6 text-indigo-400" /> AWS Bedrock Model Catalog
          </h1>
          <p className="text-gray-400 text-sm mt-1">
            Foundation models available through our unified OpenAI-compatible endpoint.
          </p>
        </div>

        {/* Search & Filters */}
        <div className="flex items-center gap-3">
          <div className="relative">
            <Search className="w-4 h-4 text-gray-500 absolute left-3 top-1/2 -translate-y-1/2" />
            <input
              type="text"
              placeholder="Search models..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              className="bg-gray-900 border border-gray-800 rounded-xl pl-9 pr-4 py-2 text-xs text-gray-200 focus:outline-none focus:border-indigo-500 w-56"
            />
          </div>

          <select
            value={filterType}
            onChange={(e) => setFilterType(e.target.value)}
            className="bg-gray-900 border border-gray-800 rounded-xl px-3 py-2 text-xs text-gray-300 focus:outline-none focus:border-indigo-500 cursor-pointer"
          >
            <option value="ALL">All Types</option>
            <option value="CHAT">Chat / LLM</option>
            <option value="IMAGE">Image Generation</option>
          </select>
        </div>
      </div>

      {/* Model Cards Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {filtered.map((m) => (
          <div
            key={m.id}
            className="rounded-2xl border border-gray-800 bg-gray-900/50 p-6 flex flex-col justify-between hover:border-indigo-500/40 transition group"
          >
            <div>
              <div className="flex items-start justify-between gap-2">
                <h3 className="font-bold text-base text-white group-hover:text-indigo-400 transition">
                  {m.name}
                </h3>
                <span className="px-2 py-0.5 rounded text-[10px] font-semibold bg-gray-800 text-gray-300 uppercase tracking-wider border border-gray-700">
                  {m.owned_by}
                </span>
              </div>

              <p className="text-gray-400 font-mono text-[11px] mt-1 break-all select-all">
                {m.id}
              </p>

              {/* Capabilities */}
              <div className="flex flex-wrap gap-1.5 mt-4">
                {m.context_window > 0 && (
                  <span className="px-2 py-0.5 rounded-md bg-indigo-950/60 border border-indigo-800/40 text-indigo-300 text-[10px] font-medium">
                    {(m.context_window / 1000).toFixed(0)}k Context
                  </span>
                )}
                {m.capabilities?.vision && (
                  <span className="px-2 py-0.5 rounded-md bg-purple-950/60 border border-purple-800/40 text-purple-300 text-[10px] font-medium flex items-center gap-1">
                    <Eye className="w-3 h-3" /> Vision
                  </span>
                )}
                {m.capabilities?.tools && (
                  <span className="px-2 py-0.5 rounded-md bg-amber-950/60 border border-amber-800/40 text-amber-300 text-[10px] font-medium flex items-center gap-1">
                    <Wrench className="w-3 h-3" /> Tool Use
                  </span>
                )}
                {m.type === "IMAGE" && (
                  <span className="px-2 py-0.5 rounded-md bg-emerald-950/60 border border-emerald-800/40 text-emerald-300 text-[10px] font-medium flex items-center gap-1">
                    <ImageIcon className="w-3 h-3" /> Image Gen
                  </span>
                )}
              </div>
            </div>

            {/* Pricing Section */}
            <div className="mt-6 pt-4 border-t border-gray-800/80">
              <div className="text-xs text-gray-400 flex items-center justify-between">
                <span>Pricing:</span>
                {m.pricing ? (
                  <span className="font-mono text-gray-200">
                    {m.type === "IMAGE" ? (
                      <strong className="text-emerald-400">${m.pricing.image_per_gen}</strong>
                    ) : (
                      <>
                        <strong className="text-emerald-400">${m.pricing.input_per_1k}</strong> / 1k in &bull;{" "}
                        <strong className="text-emerald-400">${m.pricing.output_per_1k}</strong> / 1k out
                      </>
                    )}
                  </span>
                ) : (
                  <span className="font-mono text-gray-500">Custom</span>
                )}
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
