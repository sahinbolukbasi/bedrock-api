"use client";

import React, { useState, useEffect } from "react";
import { 
  ShieldAlert, 
  Users, 
  DollarSign, 
  TrendingUp, 
  Cpu, 
  Activity, 
  Lock,
  CheckCircle2,
  XCircle
} from "lucide-react";
import { fetchApi } from "../../lib/api";

export default function AdminPage() {
  const [overview, setOverview] = useState<any>(null);
  const [users, setUsers] = useState<any[]>([]);
  const [auditLogs, setAuditLogs] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  const loadAdminData = async () => {
    try {
      const ov = await fetchApi("/api/admin/overview");
      setOverview(ov);
      const u = await fetchApi("/api/admin/users");
      setUsers(u);
      const logs = await fetchApi("/api/admin/audit-logs");
      setAuditLogs(logs);
    } catch (err) {
      console.error("Admin data load error:", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadAdminData();
  }, []);

  const toggleUserStatus = async (userId: string, currentStatus: boolean) => {
    try {
      await fetchApi(`/api/admin/users/${userId}/status?is_active=${!currentStatus}`, { method: "POST" });
      loadAdminData();
    } catch (err: any) {
      alert(err.message);
    }
  };

  if (loading) {
    return <div className="p-8 text-center text-gray-400 text-xs">Loading Admin Dashboard...</div>;
  }

  return (
    <div className="max-w-7xl mx-auto px-4 py-8">
      <div className="border-b border-gray-800 pb-6 mb-8">
        <h1 className="text-2xl font-bold text-white flex items-center gap-2">
          <ShieldAlert className="w-6 h-6 text-amber-400" /> Platform Admin Operations
        </h1>
        <p className="text-gray-400 text-sm mt-1">
          Monitor financial margins, AWS provider costs, user statuses, and audit trails.
        </p>
      </div>

      {/* Financial Metrics */}
      {overview && (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
          <div className="p-5 rounded-2xl bg-gray-900/50 border border-gray-800">
            <div className="text-gray-400 text-xs mb-1">Gross Revenue</div>
            <div className="text-2xl font-black text-white">${Number(overview.total_revenue_usd).toFixed(2)}</div>
          </div>
          <div className="p-5 rounded-2xl bg-gray-900/50 border border-gray-800">
            <div className="text-gray-400 text-xs mb-1">AWS Bedrock Cost</div>
            <div className="text-2xl font-black text-amber-400">${Number(overview.total_provider_cost_usd).toFixed(2)}</div>
          </div>
          <div className="p-5 rounded-2xl bg-gray-900/50 border border-gray-800">
            <div className="text-gray-400 text-xs mb-1">Net Platform Profit</div>
            <div className="text-2xl font-black text-emerald-400">${Number(overview.platform_net_profit_usd).toFixed(2)}</div>
          </div>
          <div className="p-5 rounded-2xl bg-gray-900/50 border border-gray-800">
            <div className="text-gray-400 text-xs mb-1">Active Users / Keys</div>
            <div className="text-2xl font-black text-indigo-400">{overview.total_users} / {overview.active_api_keys}</div>
          </div>
        </div>
      )}

      {/* User Management Table */}
      <h2 className="text-lg font-bold text-white mb-4">User Accounts & Balances</h2>
      <div className="rounded-2xl border border-gray-800 bg-gray-900/50 overflow-hidden shadow-xl mb-10">
        <table className="w-full text-left text-xs text-gray-300">
          <thead className="bg-gray-950/80 border-b border-gray-800 text-gray-400 font-semibold uppercase tracking-wider text-[10px]">
            <tr>
              <th className="px-6 py-4">User Email</th>
              <th className="px-6 py-4">Role</th>
              <th className="px-6 py-4">Wallet Balance</th>
              <th className="px-6 py-4">Status</th>
              <th className="px-6 py-4">Joined</th>
              <th className="px-6 py-4 text-right">Action</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-800/60 font-mono">
            {users.map((u) => (
              <tr key={u.id} className="hover:bg-gray-800/30 transition">
                <td className="px-6 py-4 text-white font-sans font-medium">{u.email}</td>
                <td className="px-6 py-4 uppercase text-[10px] text-gray-400">{u.role}</td>
                <td className="px-6 py-4 text-emerald-400 font-bold">${u.balance_usd.toFixed(2)}</td>
                <td className="px-6 py-4 font-sans">
                  {u.is_active ? (
                    <span className="px-2 py-0.5 rounded-full text-[10px] font-semibold bg-emerald-950 text-emerald-400 border border-emerald-800">
                      Active
                    </span>
                  ) : (
                    <span className="px-2 py-0.5 rounded-full text-[10px] font-semibold bg-red-950 text-red-400 border border-red-800">
                      Suspended
                    </span>
                  )}
                </td>
                <td className="px-6 py-4 text-gray-500 font-sans">{new Date(u.created_at).toLocaleDateString()}</td>
                <td className="px-6 py-4 text-right font-sans">
                  <button
                    onClick={() => toggleUserStatus(u.id, u.is_active)}
                    className={`px-3 py-1 rounded-lg text-xs font-medium transition ${
                      u.is_active ? "bg-red-950/60 text-red-400 border border-red-800 hover:bg-red-900" : "bg-emerald-950/60 text-emerald-400 border border-emerald-800 hover:bg-emerald-900"
                    }`}
                  >
                    {u.is_active ? "Suspend" : "Activate"}
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* Audit Logs Table */}
      <h2 className="text-lg font-bold text-white mb-4">Security & Audit Trail</h2>
      <div className="rounded-2xl border border-gray-800 bg-gray-900/50 overflow-hidden shadow-xl">
        <table className="w-full text-left text-xs text-gray-300">
          <thead className="bg-gray-950/80 border-b border-gray-800 text-gray-400 font-semibold uppercase tracking-wider text-[10px]">
            <tr>
              <th className="px-6 py-4">Action</th>
              <th className="px-6 py-4">Target Type</th>
              <th className="px-6 py-4">Resource ID</th>
              <th className="px-6 py-4 text-right">Timestamp</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-800/60 font-mono">
            {auditLogs.slice(0, 10).map((log) => (
              <tr key={log.id} className="hover:bg-gray-800/30 transition">
                <td className="px-6 py-4 text-indigo-400 font-bold">{log.action}</td>
                <td className="px-6 py-4 text-gray-300 font-sans">{log.resource_type}</td>
                <td className="px-6 py-4 text-gray-500">{log.resource_id || "N/A"}</td>
                <td className="px-6 py-4 text-right text-gray-500 font-sans">{new Date(log.created_at).toLocaleString()}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
