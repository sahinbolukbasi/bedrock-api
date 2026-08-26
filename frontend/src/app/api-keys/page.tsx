"use client";

import React, { useState, useEffect } from "react";
import { 
  Key, 
  Plus, 
  Trash2, 
  Copy, 
  Check, 
  AlertTriangle, 
  ShieldCheck,
  Clock,
  Coins
} from "lucide-react";
import { fetchApi } from "../../lib/api";
import AuthGuard from "../../components/AuthGuard";

export default function ApiKeysPage() {
  return (
    <AuthGuard>
      <ApiKeysPageContent />
    </AuthGuard>
  );
}

function ApiKeysPageContent() {
  const [keys, setKeys] = useState<any[]>([]);
  const [showModal, setShowModal] = useState(false);
  const [keyName, setKeyName] = useState("");
  const [rateLimit, setRateLimit] = useState(120);
  const [spendingLimit, setSpendingLimit] = useState<string>("");
  const [createdKey, setCreatedKey] = useState<any | null>(null);
  const [copied, setCopied] = useState(false);

  const loadKeys = async () => {
    try {
      const data = await fetchApi("/api/keys");
      setKeys(data);
    } catch (err) {
      console.error("Failed to load API keys:", err);
    }
  };

  useEffect(() => {
    loadKeys();
  }, []);

  const handleCreateKey = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      const res = await fetchApi("/api/keys", {
        method: "POST",
        body: JSON.stringify({
          name: keyName,
          rate_limit_rpm: Number(rateLimit),
          spending_limit_usd: spendingLimit ? Number(spendingLimit) : null,
        }),
      });
      setCreatedKey(res);
      setKeyName("");
      setSpendingLimit("");
      loadKeys();
    } catch (err: any) {
      alert(err.message || "Failed to create API key");
    }
  };

  const handleRevokeKey = async (keyId: string) => {
    if (!confirm("Are you sure you want to revoke this API key? This action is immediate.")) return;
    try {
      await fetchApi(`/api/keys/${keyId}/revoke`, { method: "POST" });
      loadKeys();
    } catch (err: any) {
      alert(err.message);
    }
  };

  const handleCopy = (text: string) => {
    navigator.clipboard.writeText(text);
    setCopied(true);
    setTimeout(() => setCopied(false), 2500);
  };

  return (
    <div className="max-w-6xl mx-auto px-4 py-8">
      <div className="flex items-center justify-between border-b border-gray-800 pb-6 mb-8">
        <div>
          <h1 className="text-2xl font-bold text-white flex items-center gap-2">
            <Key className="w-6 h-6 text-indigo-400" /> API Key Management
          </h1>
          <p className="text-gray-400 text-sm mt-1">
            Generate and manage secret keys to access AWS Bedrock models through our unified OpenAI-compatible endpoint.
          </p>
        </div>

        <button
          onClick={() => { setShowModal(true); setCreatedKey(null); }}
          className="flex items-center gap-2 px-4 py-2.5 rounded-xl bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-semibold transition shadow-lg shadow-indigo-600/30"
        >
          <Plus className="w-4 h-4" /> Create New Key
        </button>
      </div>

      {/* Keys Table */}
      <div className="rounded-2xl border border-gray-800 bg-gray-900/50 overflow-hidden shadow-xl">
        <table className="w-full text-left text-xs text-gray-300">
          <thead className="bg-gray-950/80 border-b border-gray-800 text-gray-400 font-semibold uppercase tracking-wider text-[10px]">
            <tr>
              <th className="px-6 py-4">Name</th>
              <th className="px-6 py-4">Secret Key Prefix</th>
              <th className="px-6 py-4">Rate Limit</th>
              <th className="px-6 py-4">Spent / Limit</th>
              <th className="px-6 py-4">Status</th>
              <th className="px-6 py-4">Created</th>
              <th className="px-6 py-4 text-right">Actions</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-800/60">
            {keys.length === 0 ? (
              <tr>
                <td colSpan={7} className="px-6 py-8 text-center text-gray-500">
                  No API keys created yet. Click "Create New Key" above to generate your first key.
                </td>
              </tr>
            ) : (
              keys.map((k) => (
                <tr key={k.id} className="hover:bg-gray-800/30 transition">
                  <td className="px-6 py-4 font-medium text-white">{k.name}</td>
                  <td className="px-6 py-4 font-mono text-gray-400">{k.prefix}...</td>
                  <td className="px-6 py-4">{k.rate_limit_rpm} req/min</td>
                  <td className="px-6 py-4 font-mono">
                    ${Number(k.spending_used_usd).toFixed(3)} / {k.spending_limit_usd ? `$${Number(k.spending_limit_usd).toFixed(2)}` : "∞"}
                  </td>
                  <td className="px-6 py-4">
                    {k.is_active ? (
                      <span className="px-2 py-0.5 rounded-full text-[10px] font-semibold bg-emerald-950 text-emerald-400 border border-emerald-800">
                        Active
                      </span>
                    ) : (
                      <span className="px-2 py-0.5 rounded-full text-[10px] font-semibold bg-red-950 text-red-400 border border-red-800">
                        Revoked
                      </span>
                    )}
                  </td>
                  <td className="px-6 py-4 text-gray-500">
                    {new Date(k.created_at).toLocaleDateString()}
                  </td>
                  <td className="px-6 py-4 text-right">
                    {k.is_active && (
                      <button
                        onClick={() => handleRevokeKey(k.id)}
                        className="text-gray-400 hover:text-red-400 transition"
                        title="Revoke Key"
                      >
                        <Trash2 className="w-4 h-4 inline" />
                      </button>
                    )}
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>

      {/* Creation Modal */}
      {showModal && (
        <div className="fixed inset-0 bg-black/70 backdrop-blur-sm flex items-center justify-center p-4 z-50 animate-in fade-in">
          <div className="bg-gray-900 border border-gray-800 rounded-2xl max-w-md w-full p-6 shadow-2xl">
            {!createdKey ? (
              <form onSubmit={handleCreateKey}>
                <h3 className="text-lg font-bold text-white">Create Secret API Key</h3>
                <p className="text-gray-400 text-xs mt-1 mb-4">
                  Enter a label and optional spending limits for this key.
                </p>

                <div className="space-y-4 text-xs">
                  <div>
                    <label className="block text-gray-300 font-medium mb-1">Key Name</label>
                    <input
                      type="text"
                      required
                      placeholder="e.g. Production Backend, Local Testing"
                      value={keyName}
                      onChange={(e) => setKeyName(e.target.value)}
                      className="w-full bg-gray-950 border border-gray-800 rounded-xl p-2.5 text-gray-200 focus:outline-none focus:border-indigo-500"
                    />
                  </div>

                  <div className="grid grid-cols-2 gap-3">
                    <div>
                      <label className="block text-gray-300 font-medium mb-1">Rate Limit (RPM)</label>
                      <input
                        type="number"
                        min="1"
                        max="10000"
                        value={rateLimit}
                        onChange={(e) => setRateLimit(Number(e.target.value))}
                        className="w-full bg-gray-950 border border-gray-800 rounded-xl p-2.5 text-gray-200 focus:outline-none focus:border-indigo-500"
                      />
                    </div>

                    <div>
                      <label className="block text-gray-300 font-medium mb-1">Spending Limit ($)</label>
                      <input
                        type="number"
                        step="0.1"
                        placeholder="Unlimited"
                        value={spendingLimit}
                        onChange={(e) => setSpendingLimit(e.target.value)}
                        className="w-full bg-gray-950 border border-gray-800 rounded-xl p-2.5 text-gray-200 focus:outline-none focus:border-indigo-500"
                      />
                    </div>
                  </div>
                </div>

                <div className="mt-6 flex justify-end gap-3">
                  <button
                    type="button"
                    onClick={() => setShowModal(false)}
                    className="px-4 py-2 rounded-xl bg-gray-800 hover:bg-gray-700 text-gray-300 text-xs font-semibold transition"
                  >
                    Cancel
                  </button>
                  <button
                    type="submit"
                    className="px-4 py-2 rounded-xl bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-semibold transition"
                  >
                    Create Key
                  </button>
                </div>
              </form>
            ) : (
              <div>
                <div className="w-10 h-10 rounded-xl bg-emerald-950 border border-emerald-800 flex items-center justify-center text-emerald-400 mb-3">
                  <ShieldCheck className="w-5 h-5" />
                </div>
                <h3 className="text-lg font-bold text-white">API Key Created!</h3>
                <p className="text-gray-400 text-xs mt-1 mb-4">
                  Please copy your secret key now. <strong className="text-amber-400">You will not be able to see it again!</strong>
                </p>

                <div className="bg-gray-950 border border-gray-800 rounded-xl p-3 flex items-center justify-between gap-2 mb-4 font-mono text-xs text-indigo-300 break-all select-all">
                  <span>{createdKey.api_key}</span>
                  <button
                    onClick={() => handleCopy(createdKey.api_key)}
                    className="p-2 bg-indigo-600/30 hover:bg-indigo-600/50 rounded-lg text-white transition shrink-0"
                    title="Copy Key"
                  >
                    {copied ? <Check className="w-4 h-4 text-emerald-400" /> : <Copy className="w-4 h-4" />}
                  </button>
                </div>

                <div className="flex justify-end">
                  <button
                    onClick={() => setShowModal(false)}
                    className="px-4 py-2 rounded-xl bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-semibold transition"
                  >
                    I Have Saved My Key
                  </button>
                </div>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
