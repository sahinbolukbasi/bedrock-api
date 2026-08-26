"use client";

import React, { useState, useEffect } from "react";
import { 
  CreditCard, 
  Wallet, 
  Sparkles, 
  ArrowUpRight, 
  Clock, 
  CheckCircle2, 
  PlusCircle,
  ShieldCheck
} from "lucide-react";
import { fetchApi } from "@/lib/api";

export default function BillingPage() {
  const [balance, setBalance] = useState<number>(0);
  const [packages, setPackages] = useState<any[]>([]);
  const [transactions, setTransactions] = useState<any[]>([]);
  const [loadingPkg, setLoadingPkg] = useState<string | null>(null);

  const loadBillingData = async () => {
    try {
      const wData = await fetchApi("/api/wallet");
      setBalance(Number(wData.balance_usd));
      const pData = await fetchApi("/api/wallet/packages");
      setPackages(pData);
      const tData = await fetchApi("/api/wallet/transactions");
      setTransactions(tData);
    } catch (err) {
      console.error("Failed to load billing info:", err);
    }
  };

  useEffect(() => {
    loadBillingData();
  }, []);

  const handlePurchase = async (pkgId: string) => {
    setLoadingPkg(pkgId);
    try {
      const res = await fetchApi("/api/wallet/checkout", {
        method: "POST",
        body: JSON.stringify({ package_id: pkgId }),
      });
      if (res.checkout_url) {
        window.location.href = res.checkout_url;
      }
    } catch (err: any) {
      alert(err.message || "Failed to initiate Stripe Checkout.");
      setLoadingPkg(null);
    }
  };

  const handleDevFund = async () => {
    try {
      const res = await fetchApi("/api/wallet/dev-fund", { method: "POST" });
      alert(res.message);
      loadBillingData();
    } catch (err: any) {
      alert(err.message);
    }
  };

  return (
    <div className="max-w-6xl mx-auto px-4 py-8">
      {/* Balance Card Banner */}
      <div className="rounded-3xl bg-gradient-to-r from-indigo-900/40 via-purple-900/40 to-gray-900 border border-indigo-500/30 p-8 mb-10 shadow-2xl relative overflow-hidden">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-6 relative z-10">
          <div>
            <div className="flex items-center gap-2 text-indigo-300 text-xs font-semibold uppercase tracking-wider mb-2">
              <Wallet className="w-4 h-4" /> Available Credit Balance
            </div>
            <div className="text-4xl sm:text-5xl font-black text-white tracking-tight">
              ${balance.toFixed(4)} <span className="text-sm font-normal text-gray-400 font-mono">USD</span>
            </div>
            <p className="text-gray-400 text-xs mt-2">
              All API requests and model invocations are metered and deducted atomically from this balance.
            </p>
          </div>

          <div className="flex items-center gap-3">
            <button
              onClick={handleDevFund}
              className="px-4 py-3 rounded-xl bg-gray-900 hover:bg-gray-800 border border-gray-700 text-indigo-300 text-xs font-semibold transition flex items-center gap-1.5 shadow-md"
            >
              <PlusCircle className="w-4 h-4 text-emerald-400" /> Dev Fast-Fund (+$10)
            </button>
          </div>
        </div>
      </div>

      {/* Credit Packages Grid */}
      <div className="mb-12">
        <h2 className="text-xl font-bold text-white mb-2">Purchase Credit Packages</h2>
        <p className="text-gray-400 text-xs mb-6">
          Payments are securely processed via Stripe. Purchased credits never expire.
        </p>

        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-4">
          {packages.map((p) => (
            <div
              key={p.package_id}
              className="rounded-2xl border border-gray-800 bg-gray-900/60 p-5 flex flex-col justify-between hover:border-indigo-500/50 transition relative group"
            >
              <div>
                <h3 className="font-semibold text-sm text-white">{p.name}</h3>
                <div className="text-2xl font-black text-white mt-2">
                  ${Number(p.amount_usd).toFixed(0)}
                </div>
                {Number(p.bonus_usd) > 0 && (
                  <span className="inline-block mt-1 px-2 py-0.5 rounded text-[10px] font-bold bg-amber-950 text-amber-300 border border-amber-800">
                    +${Number(p.bonus_usd).toFixed(2)} Bonus
                  </span>
                )}
                <div className="text-xs text-gray-400 mt-3">
                  Total credit: <strong className="text-emerald-400">${Number(p.total_credits).toFixed(2)}</strong>
                </div>
              </div>

              <button
                onClick={() => handlePurchase(p.package_id)}
                disabled={loadingPkg === p.package_id}
                className="mt-6 w-full py-2.5 rounded-xl bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-semibold transition flex items-center justify-center gap-1 shadow-md shadow-indigo-600/20"
              >
                {loadingPkg === p.package_id ? "Redirecting..." : "Checkout"}
                <ArrowUpRight className="w-3.5 h-3.5" />
              </button>
            </div>
          ))}
        </div>
      </div>

      {/* Transactions Ledger */}
      <div>
        <h2 className="text-lg font-bold text-white mb-4">Transaction Ledger</h2>
        <div className="rounded-2xl border border-gray-800 bg-gray-900/50 overflow-hidden shadow-xl">
          <table className="w-full text-left text-xs text-gray-300">
            <thead className="bg-gray-950/80 border-b border-gray-800 text-gray-400 font-semibold uppercase tracking-wider text-[10px]">
              <tr>
                <th className="px-6 py-4">Transaction ID</th>
                <th className="px-6 py-4">Type</th>
                <th className="px-6 py-4">Description</th>
                <th className="px-6 py-4">Amount</th>
                <th className="px-6 py-4">Balance After</th>
                <th className="px-6 py-4 text-right">Date</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-800/60 font-mono">
              {transactions.length === 0 ? (
                <tr>
                  <td colSpan={6} className="px-6 py-8 text-center text-gray-500 font-sans">
                    No transactions recorded yet.
                  </td>
                </tr>
              ) : (
                transactions.map((t) => {
                  const isPositive = Number(t.amount_usd) > 0;
                  return (
                    <tr key={t.id} className="hover:bg-gray-800/30 transition">
                      <td className="px-6 py-4 text-gray-500 font-mono">{t.id.slice(0, 14)}...</td>
                      <td className="px-6 py-4">
                        <span className={`px-2 py-0.5 rounded text-[10px] font-semibold ${
                          isPositive
                            ? "bg-emerald-950 text-emerald-400 border border-emerald-800"
                            : "bg-gray-800 text-gray-300 border border-gray-700"
                        }`}>
                          {t.type}
                        </span>
                      </td>
                      <td className="px-6 py-4 text-gray-300 font-sans">{t.description || "N/A"}</td>
                      <td className={`px-6 py-4 font-bold ${isPositive ? "text-emerald-400" : "text-gray-300"}`}>
                        {isPositive ? `+$${Number(t.amount_usd).toFixed(4)}` : `-$${Math.abs(Number(t.amount_usd)).toFixed(5)}`}
                      </td>
                      <td className="px-6 py-4 text-gray-400">${Number(t.balance_after).toFixed(4)}</td>
                      <td className="px-6 py-4 text-right text-gray-500 font-sans">
                        {new Date(t.created_at).toLocaleString()}
                      </td>
                    </tr>
                  );
                })
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
