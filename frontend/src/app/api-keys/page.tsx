"use client";

import React, { useState, useEffect } from "react";
import Link from "next/link";
import { 
  Key, 
  Plus, 
  Trash2, 
  Copy, 
  Check, 
  ShieldCheck,
  ShieldAlert,
  Edit3,
  Sliders,
  Activity,
  Globe,
  RefreshCw,
  X,
  ArrowLeft
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

  // Edit Modal
  const [editingKey, setEditingKey] = useState<any | null>(null);
  const [editKeyName, setEditKeyName] = useState("");
  const [editSpendingLimit, setEditSpendingLimit] = useState<string>("");
  const [editRpm, setEditRpm] = useState<number>(120);

  const loadKeys = async () => {
    try {
      const data = await fetchApi("/api/keys");
      setKeys(data || []);
    } catch (err) {
      console.error("Failed to load API keys:", err);
    }
  };

  useEffect(() => {
    loadKeys();
  }, []);

  const handleCreateKey = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!keyName.trim()) return;
    try {
      const res = await fetchApi("/api/keys", {
        method: "POST",
        body: JSON.stringify({
          name: keyName.trim(),
          rate_limit_rpm: Number(rateLimit) || 120,
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

  const handleOpenEdit = (k: any) => {
    setEditingKey(k);
    setEditKeyName(k.name || "");
    setEditSpendingLimit(k.spending_limit_usd ? String(Number(k.spending_limit_usd)) : "");
    setEditRpm(k.rate_limit_rpm || 120);
  };

  const handleUpdateKey = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!editingKey) return;
    try {
      await fetchApi(`/api/keys/${editingKey.id}`, {
        method: "PATCH",
        body: JSON.stringify({
          name: editKeyName.trim() || editingKey.name,
          rate_limit_rpm: Number(editRpm) || 120,
          spending_limit_usd: editSpendingLimit ? Number(editSpendingLimit) : null,
        }),
      });
      setEditingKey(null);
      loadKeys();
    } catch (err: any) {
      alert(err.message || "Failed to update API key");
    }
  };

  const handleRevokeKey = async (keyId: string) => {
    if (!confirm("Bu API anahtarını devre dışı bırakmak istediğinize emin misiniz?")) return;
    try {
      await fetchApi(`/api/keys/${keyId}/revoke`, { method: "POST" });
      loadKeys();
    } catch (err: any) {
      alert(err.message);
    }
  };

  const handleDeleteKey = async (keyId: string) => {
    if (!confirm("Bu API anahtarını kalıcı olarak silmek istediğinize emin misiniz?")) return;
    try {
      await fetchApi(`/api/keys/${keyId}`, { method: "DELETE" });
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
    <div className="max-w-6xl mx-auto px-4 py-8 space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-slate-200 dark:border-gray-800 pb-6">
        <div>
          <Link href="/?tab=api" className="inline-flex items-center gap-1.5 text-xs text-indigo-500 hover:text-indigo-400 font-bold mb-2 transition">
            <ArrowLeft className="w-3.5 h-3.5" /> Ana Konsola & Entegrasyon Kılavuzuna Dön
          </Link>
          <h1 className="text-2xl font-black text-slate-900 dark:text-white flex items-center gap-2.5">
            <Key className="w-6 h-6 text-indigo-600 dark:text-indigo-400" />
            <span>API Anahtarları & Bütçe Yönetimi</span>
          </h1>
          <p className="text-slate-500 dark:text-gray-400 text-xs mt-1">
            AWS Bedrock modellerine erişmek için gizli API anahtarları üretin, harcama limitleri koyun ve yönetin.
          </p>
        </div>

        <button
          onClick={() => { setShowModal(true); setCreatedKey(null); }}
          className="flex items-center gap-2 px-4 py-2.5 rounded-xl bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-bold transition shadow-lg shadow-indigo-600/25"
        >
          <Plus className="w-4 h-4" /> Yeni Anahtar Üret
        </button>
      </div>

      {/* Keys Table */}
      <div className="rounded-3xl border border-slate-200 dark:border-gray-800 bg-white dark:bg-gray-900 overflow-hidden shadow-sm">
        <div className="p-4 border-b border-slate-200 dark:border-gray-800 flex items-center justify-between">
          <span className="font-bold text-xs text-slate-900 dark:text-white">
            Aktif API Anahtarlarınız ({keys.length})
          </span>
          <button onClick={loadKeys} className="p-1.5 text-slate-400 hover:text-white transition">
            <RefreshCw className="w-4 h-4" />
          </button>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs text-slate-700 dark:text-gray-300">
            <thead className="bg-slate-50 dark:bg-gray-950 border-b border-slate-200 dark:border-gray-800 text-slate-400 font-bold uppercase tracking-wider text-[10px]">
              <tr>
                <th className="px-6 py-4">Anahtar Adı</th>
                <th className="px-6 py-4">Prefix</th>
                <th className="px-6 py-4">Hız Limiti</th>
                <th className="px-6 py-4">Harcanan / Bütçe Kısıtı</th>
                <th className="px-6 py-4">Durum</th>
                <th className="px-6 py-4">Oluşturulma</th>
                <th className="px-6 py-4 text-right">İşlemler</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100 dark:divide-gray-800/60 font-medium">
              {keys.length === 0 ? (
                <tr>
                  <td colSpan={7} className="px-6 py-8 text-center text-slate-500">
                    Henüz kayıtlı bir API anahtarınız yok. "Yeni Anahtar Üret" butonuna tıklayarak oluşturabilirsiniz.
                  </td>
                </tr>
              ) : (
                keys.map((k) => {
                  const used = Number(k.spending_used_usd || 0);
                  const limit = k.spending_limit_usd ? Number(k.spending_limit_usd) : null;
                  const pct = limit ? Math.min(100, Math.round((used / limit) * 100)) : null;

                  return (
                    <tr key={k.id} className="hover:bg-slate-50/60 dark:hover:bg-gray-800/30 transition">
                      <td className="px-6 py-4 font-bold text-slate-900 dark:text-white">{k.name}</td>
                      <td className="px-6 py-4 font-mono text-slate-400">{k.prefix}••••••••</td>
                      <td className="px-6 py-4 font-mono">{k.rate_limit_rpm || 120} req/dk</td>
                      <td className="px-6 py-4 min-w-[180px]">
                        <div className="font-mono text-[11px] mb-1">
                          ${used.toFixed(4)} / {limit ? `$${limit.toFixed(2)}` : "Limitsiz (∞)"}
                        </div>
                        {limit && (
                          <div className="w-full h-1.5 bg-slate-100 dark:bg-gray-800 rounded-full overflow-hidden">
                            <div
                              className={`h-full rounded-full ${
                                (pct || 0) > 90 ? "bg-red-500" : (pct || 0) > 60 ? "bg-amber-500" : "bg-emerald-500"
                              }`}
                              style={{ width: `${pct}%` }}
                            />
                          </div>
                        )}
                      </td>
                      <td className="px-6 py-4">
                        {k.is_active ? (
                          <span className="px-2.5 py-0.5 rounded-full text-[10px] font-bold bg-emerald-500/10 text-emerald-600 border border-emerald-500/20">
                            Aktif
                          </span>
                        ) : (
                          <span className="px-2.5 py-0.5 rounded-full text-[10px] font-bold bg-red-500/10 text-red-600 border border-red-500/20">
                            İptal
                          </span>
                        )}
                      </td>
                      <td className="px-6 py-4 text-slate-500 text-[11px]">
                        {k.created_at ? new Date(k.created_at).toLocaleDateString("tr-TR") : "—"}
                      </td>
                      <td className="px-6 py-4 text-right">
                        <div className="flex items-center justify-end gap-1.5">
                          <button
                            type="button"
                            onClick={() => handleOpenEdit(k)}
                            className="p-1.5 text-slate-400 hover:text-indigo-600 transition"
                            title="Bütçe Kısıtını Düzenle"
                          >
                            <Edit3 className="w-4 h-4" />
                          </button>
                          {k.is_active && (
                            <button
                              type="button"
                              onClick={() => handleRevokeKey(k.id)}
                              className="p-1.5 text-slate-400 hover:text-amber-600 transition"
                              title="İptal Et"
                            >
                              <ShieldAlert className="w-4 h-4" />
                            </button>
                          )}
                          <button
                            type="button"
                            onClick={() => handleDeleteKey(k.id)}
                            className="p-1.5 text-slate-400 hover:text-red-600 transition"
                            title="Sil"
                          >
                            <Trash2 className="w-4 h-4" />
                          </button>
                        </div>
                      </td>
                    </tr>
                  );
                })
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* Creation Modal */}
      {showModal && (
        <div className="fixed inset-0 bg-black/70 backdrop-blur-sm flex items-center justify-center p-4 z-50 animate-in fade-in">
          <div className="bg-white dark:bg-gray-900 border border-slate-200 dark:border-gray-800 rounded-3xl max-w-md w-full p-6 shadow-2xl space-y-4">
            {!createdKey ? (
              <form onSubmit={handleCreateKey} className="space-y-4">
                <div className="flex items-center justify-between border-b border-slate-100 dark:border-gray-800 pb-3">
                  <h3 className="text-base font-bold text-slate-900 dark:text-white">Yeni API Anahtarı Üret</h3>
                  <button type="button" onClick={() => setShowModal(false)} className="text-slate-400 hover:text-white">
                    <X className="w-4 h-4" />
                  </button>
                </div>

                <div>
                  <label className="block text-xs font-bold text-slate-700 dark:text-gray-300 mb-1">Anahtar Adı</label>
                  <input
                    type="text"
                    required
                    placeholder="Örn: Production Backend, Cursor IDE"
                    value={keyName}
                    onChange={(e) => setKeyName(e.target.value)}
                    className="w-full bg-slate-50 dark:bg-gray-950 border border-slate-200 dark:border-gray-800 rounded-xl px-3.5 py-2.5 text-xs text-slate-900 dark:text-white focus:outline-none focus:border-indigo-500"
                  />
                </div>

                <div className="grid grid-cols-2 gap-3">
                  <div>
                    <label className="block text-xs font-bold text-slate-700 dark:text-gray-300 mb-1">Hız Limiti (RPM)</label>
                    <select
                      value={rateLimit}
                      onChange={(e) => setRateLimit(Number(e.target.value))}
                      className="w-full bg-slate-50 dark:bg-gray-950 border border-slate-200 dark:border-gray-800 rounded-xl px-3 py-2 text-xs text-slate-900 dark:text-white focus:outline-none"
                    >
                      <option value={60}>60 RPM</option>
                      <option value={120}>120 RPM</option>
                      <option value={300}>300 RPM</option>
                      <option value={600}>600 RPM</option>
                    </select>
                  </div>

                  <div>
                    <label className="block text-xs font-bold text-slate-700 dark:text-gray-300 mb-1">Bütçe Kısıtı ($ USD)</label>
                    <input
                      type="number"
                      step="0.5"
                      placeholder="Limitsiz (∞)"
                      value={spendingLimit}
                      onChange={(e) => setSpendingLimit(e.target.value)}
                      className="w-full bg-slate-50 dark:bg-gray-950 border border-slate-200 dark:border-gray-800 rounded-xl px-3 py-2 text-xs text-slate-900 dark:text-white font-mono focus:outline-none focus:border-indigo-500"
                    />
                  </div>
                </div>

                <div className="flex justify-end gap-2 pt-2">
                  <button
                    type="button"
                    onClick={() => setShowModal(false)}
                    className="px-4 py-2 rounded-xl bg-slate-100 dark:bg-gray-800 text-xs font-bold text-slate-700 dark:text-gray-300"
                  >
                    İptal
                  </button>
                  <button
                    type="submit"
                    className="px-5 py-2 rounded-xl bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-bold transition shadow-md shadow-indigo-600/25"
                  >
                    Anahtar Üret
                  </button>
                </div>
              </form>
            ) : (
              <div className="space-y-4">
                <div className="w-10 h-10 rounded-2xl bg-emerald-500/10 border border-emerald-500/30 flex items-center justify-center text-emerald-500">
                  <ShieldCheck className="w-5 h-5" />
                </div>
                <div>
                  <h3 className="text-base font-bold text-slate-900 dark:text-white">API Anahtarınız Hazır!</h3>
                  <p className="text-slate-500 dark:text-gray-400 text-xs mt-0.5">
                    Lütfen anahtarınızı güvenli bir yere kaydedin. Bu anahtar bir daha gösterilmeyecektir.
                  </p>
                </div>

                <div className="bg-slate-50 dark:bg-gray-950 border border-slate-200 dark:border-gray-800 rounded-2xl p-3 flex items-center justify-between gap-2 font-mono text-xs text-indigo-600 dark:text-indigo-400 break-all select-all font-bold">
                  <span>{createdKey.api_key}</span>
                  <button
                    onClick={() => handleCopy(createdKey.api_key)}
                    className="p-2 bg-indigo-600 hover:bg-indigo-500 rounded-xl text-white transition shrink-0"
                    title="Kopyala"
                  >
                    {copied ? <Check className="w-4 h-4" /> : <Copy className="w-4 h-4" />}
                  </button>
                </div>

                <div className="flex justify-end pt-2">
                  <button
                    onClick={() => setShowModal(false)}
                    className="px-5 py-2.5 rounded-xl bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-bold transition"
                  >
                    Kaydettim, Kapat
                  </button>
                </div>
              </div>
            )}
          </div>
        </div>
      )}

      {/* Edit Modal */}
      {editingKey && (
        <div className="fixed inset-0 bg-black/70 backdrop-blur-sm flex items-center justify-center p-4 z-50 animate-in fade-in">
          <div className="bg-white dark:bg-gray-900 border border-slate-200 dark:border-gray-800 rounded-3xl max-w-md w-full p-6 shadow-2xl space-y-4">
            <div className="flex items-center justify-between border-b border-slate-100 dark:border-gray-800 pb-3">
              <h3 className="text-base font-bold text-slate-900 dark:text-white flex items-center gap-2">
                <Sliders className="w-4 h-4 text-indigo-600" />
                <span>Bütçe Kısıtını & Anahtarı Düzenle</span>
              </h3>
              <button type="button" onClick={() => setEditingKey(null)} className="text-slate-400 hover:text-white">
                <X className="w-4 h-4" />
              </button>
            </div>

            <form onSubmit={handleUpdateKey} className="space-y-4">
              <div>
                <label className="block text-xs font-bold text-slate-700 dark:text-gray-300 mb-1">Anahtar Adı</label>
                <input
                  type="text"
                  required
                  value={editKeyName}
                  onChange={(e) => setEditKeyName(e.target.value)}
                  className="w-full bg-slate-50 dark:bg-gray-950 border border-slate-200 dark:border-gray-800 rounded-xl px-3.5 py-2.5 text-xs text-slate-900 dark:text-white focus:outline-none focus:border-indigo-500 font-medium"
                />
              </div>

              <div>
                <label className="block text-xs font-bold text-slate-700 dark:text-gray-300 mb-1 flex items-center justify-between">
                  <span>Bütçe Kısıtı ($ USD)</span>
                  <span className="text-[10px] text-slate-400 font-normal">Boş = Limitsiz</span>
                </label>
                <input
                  type="number"
                  step="0.5"
                  placeholder="Limitsiz (∞)"
                  value={editSpendingLimit}
                  onChange={(e) => setEditSpendingLimit(e.target.value)}
                  className="w-full bg-slate-50 dark:bg-gray-950 border border-slate-200 dark:border-gray-800 rounded-xl px-3.5 py-2.5 text-xs text-slate-900 dark:text-white font-mono focus:outline-none focus:border-indigo-500"
                />
              </div>

              <div>
                <label className="block text-xs font-bold text-slate-700 dark:text-gray-300 mb-1">Hız Limiti (RPM)</label>
                <select
                  value={editRpm}
                  onChange={(e) => setEditRpm(Number(e.target.value))}
                  className="w-full bg-slate-50 dark:bg-gray-950 border border-slate-200 dark:border-gray-800 rounded-xl px-3 py-2 text-xs text-slate-900 dark:text-white focus:outline-none"
                >
                  <option value={60}>60 RPM</option>
                  <option value={120}>120 RPM</option>
                  <option value={300}>300 RPM</option>
                  <option value={600}>600 RPM</option>
                </select>
              </div>

              <div className="flex justify-end gap-2 pt-2">
                <button
                  type="button"
                  onClick={() => setEditingKey(null)}
                  className="px-4 py-2 rounded-xl bg-slate-100 dark:bg-gray-800 text-xs font-bold text-slate-700 dark:text-gray-300"
                >
                  İptal
                </button>
                <button
                  type="submit"
                  className="px-5 py-2 rounded-xl bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-bold shadow-md shadow-indigo-600/20"
                >
                  Kaydet
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
