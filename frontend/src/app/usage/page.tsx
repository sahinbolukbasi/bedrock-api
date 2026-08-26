"use client";

import React, { useState, useEffect } from "react";
import { BarChart3, Activity, Coins, Layers, Zap } from "lucide-react";
import { fetchApi } from "@/lib/api";

export default function UsagePage() {
  const [summary, setSummary] = useState<any>({
    total_spent_usd: 0,
    total_requests: 0,
    input_tokens: 0,
    output_tokens: 0,
    total_tokens: 0,
  });
  const [recentActivity, setRecentActivity] = useState<any[]>([]);

  useEffect(() => {
    async function loadUsage() {
      try {
        const sumData = await fetchApi("/api/usage/summary");
        setSummary(sumData);
        const actData = await fetchApi("/api/usage/recent");
        setRecentActivity(actData);
      } catch (err) {
        console.error("Failed to load usage metrics:", err);
      }
    }
    loadUsage();
  }, []);

  return (
    <div className="max-w-6xl mx-auto px-4 py-8">
      <div className="border-b border-gray-800 pb-6 mb-8">
        <h1 className="text-2xl font-bold text-white flex items-center gap-2">
          <BarChart3 className="w-6 h-6 text-indigo-400" /> Usage & Analytics
        </h1>
        <p className="text-gray-400 text-sm mt-1">
          Detailed metrics, token consumption, and audit trail for your API requests.
        </p>
      </div>

      {/* Overview Stat Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
        <div className="p-5 rounded-2xl bg-gray-900/50 border border-gray-800">
          <div className="flex items-center justify-between text-gray-400 text-xs mb-2">
            <span>Total Spent</span>
            <Coins className="w-4 h-4 text-emerald-400" />
          </div>
          <div className="text-2xl font-extrabold text-white">
            ${Number(summary.total_spent_usd).toFixed(4)}
          </div>
        </div>

        <div className="p-5 rounded-2xl bg-gray-900/50 border border-gray-800">
          <div className="flex items-center justify-between text-gray-400 text-xs mb-2">
            <span>Total Requests</span>
            <Activity className="w-4 h-4 text-indigo-400" />
          </div>
          <div className="text-2xl font-extrabold text-white">
            {summary.total_requests.toLocaleString()}
          </div>
        </div>

        <div className="p-5 rounded-2xl bg-gray-900/50 border border-gray-800">
          <div className="flex items-center justify-between text-gray-400 text-xs mb-2">
            <span>Total Tokens</span>
            <Layers className="w-4 h-4 text-purple-400" />
          </div>
          <div className="text-2xl font-extrabold text-white">
            {summary.total_tokens.toLocaleString()}
          </div>
        </div>

        <div className="p-5 rounded-2xl bg-gray-900/50 border border-gray-800">
          <div className="flex items-center justify-between text-gray-400 text-xs mb-2">
            <span>Token Split (In / Out)</span>
            <Zap className="w-4 h-4 text-amber-400" />
          </div>
          <div className="text-sm font-mono text-gray-300 mt-2">
            <span className="text-indigo-400">{summary.input_tokens.toLocaleString()}</span> /{" "}
            <span className="text-purple-400">{summary.output_tokens.toLocaleString()}</span>
          </div>
        </div>
      </div>

      {/* Recent Activity Table */}
      <h2 className="text-lg font-bold text-white mb-4">Recent API Activity</h2>
      <div className="rounded-2xl border border-gray-800 bg-gray-900/50 overflow-hidden shadow-xl">
        <table className="w-full text-left text-xs text-gray-300">
          <thead className="bg-gray-950/80 border-b border-gray-800 text-gray-400 font-semibold uppercase tracking-wider text-[10px]">
            <tr>
              <th className="px-6 py-4">Request ID</th>
              <th className="px-6 py-4">Model</th>
              <th className="px-6 py-4">Tokens</th>
              <th className="px-6 py-4">Charged ($)</th>
              <th className="px-6 py-4">Latency</th>
              <th className="px-6 py-4">Status</th>
              <th className="px-6 py-4 text-right">Time</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-800/60 font-mono">
            {recentActivity.length === 0 ? (
              <tr>
                <td colSpan={7} className="px-6 py-8 text-center text-gray-500 font-sans">
                  No activity recorded yet. Send a request from the chat playground or via API.
                </td>
              </tr>
            ) : (
              recentActivity.map((r) => (
                <tr key={r.request_id} className="hover:bg-gray-800/30 transition">
                  <td className="px-6 py-4 text-gray-400">{r.request_id.slice(0, 16)}...</td>
                  <td className="px-6 py-4 text-white font-sans">{r.model_name}</td>
                  <td className="px-6 py-4">{r.total_tokens}</td>
                  <td className="px-6 py-4 text-emerald-400 font-semibold">${Number(r.customer_charged_usd).toFixed(5)}</td>
                  <td className="px-6 py-4 text-gray-400">{r.duration_ms}ms</td>
                  <td className="px-6 py-4">
                    <span className="px-2 py-0.5 rounded text-[10px] font-semibold bg-emerald-950 text-emerald-400 border border-emerald-800">
                      {r.status_code} OK
                    </span>
                  </td>
                  <td className="px-6 py-4 text-right text-gray-500 font-sans">
                    {new Date(r.created_at).toLocaleTimeString()}
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}
