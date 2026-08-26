"use client";

import React, { useState, useEffect } from "react";
import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { 
  LogOut, 
  Wallet,
  User as UserIcon,
  ShieldAlert,
  Sparkles,
  Activity,
  Cpu,
  RefreshCw
} from "lucide-react";
import { getAuthToken, clearAuthToken, fetchApi } from "../lib/api";
import ThemeToggle from "./ThemeToggle";

export default function Navigation() {
  const pathname = usePathname();
  const router = useRouter();
  const [balance, setBalance] = useState<number | null>(null);
  const [userEmail, setUserEmail] = useState<string | null>(null);
  const [userRole, setUserRole] = useState<string>("user");
  const [isLoggedIn, setIsLoggedIn] = useState<boolean>(false);

  const loadUserState = async () => {
    const token = getAuthToken();
    if (!token) {
      setIsLoggedIn(false);
      setBalance(null);
      setUserEmail(null);
      return;
    }
    setIsLoggedIn(true);
    try {
      const walletData = await fetchApi("/api/wallet");
      if (walletData && walletData.balance_usd !== undefined) {
        setBalance(Number(walletData.balance_usd));
      }
      const userProfile = await fetchApi("/api/auth/me");
      if (userProfile) {
        setUserEmail(userProfile.email || null);
        setUserRole(userProfile.role || "user");
      }
    } catch (err) {
      console.error("Failed to load user info:", err);
    }
  };

  useEffect(() => {
    loadUserState();
  }, [pathname]);

  const handleLogout = () => {
    clearAuthToken();
    setIsLoggedIn(false);
    setBalance(null);
    setUserEmail(null);
    router.push("/");
    window.location.reload();
  };

  return (
    <header className="w-full border-b border-slate-200 dark:border-gray-800/80 bg-white/95 dark:bg-[#0b0f17]/95 backdrop-blur-md sticky top-0 z-50 transition-colors">
      <div className="w-full px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-16">
          
          {/* Sol Logo ve AWS Durum Alanı */}
          <div className="flex items-center gap-3 sm:gap-4 shrink-0">
            <Link href="/" className="flex items-center gap-2.5 group">
              <div className="w-9 h-9 rounded-xl bg-gradient-to-tr from-indigo-500 via-purple-500 to-amber-500 p-[2px] shadow-sm group-hover:scale-105 transition transform">
                <div className="w-full h-full bg-white dark:bg-gray-950 rounded-[10px] flex items-center justify-center font-black text-slate-900 dark:text-white text-xs">
                  ⚡
                </div>
              </div>
              <div className="flex flex-col">
                <div className="flex items-center gap-1.5">
                  <span className="font-extrabold text-sm sm:text-base text-slate-900 dark:text-white tracking-tight group-hover:text-indigo-600 dark:group-hover:text-indigo-400 transition">
                    Bedrock<span className="text-amber-500">Gateway</span>
                  </span>
                  <span className="hidden sm:inline-block px-1.5 py-0.5 text-[9px] font-black bg-indigo-50 text-indigo-700 dark:bg-indigo-950 dark:text-indigo-300 border border-indigo-200 dark:border-indigo-800 rounded uppercase">
                    PRO
                  </span>
                </div>
                <span className="text-[10px] text-slate-400 dark:text-gray-500 font-medium hidden md:inline">
                  AWS Bedrock Enterprise Platform
                </span>
              </div>
            </Link>

            {/* AWS Canlı Durum Rozeti */}
            <div className="hidden lg:flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-emerald-50 dark:bg-emerald-950/50 border border-emerald-200 dark:border-emerald-800 text-[11px] font-bold text-emerald-700 dark:text-emerald-300">
              <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse" />
              <span>AWS us-east-1 Live</span>
            </div>
          </div>

          {/* Sağ Eylem & Profil Barı */}
          <div className="flex items-center gap-2 sm:gap-3 shrink-0">
            
            {/* Canlı Grafana Linki (Admin ise) */}
            {isLoggedIn && userRole === "admin" && (
              <a
                href="http://bedrock-gateway-alb-664380835.us-east-1.elb.amazonaws.com:3001"
                target="_blank"
                rel="noreferrer"
                className="hidden md:flex items-center gap-1 px-2.5 py-1 rounded-xl bg-amber-500/10 border border-amber-500/30 text-amber-600 dark:text-amber-400 text-xs font-bold hover:bg-amber-500/20 transition"
              >
                <Activity className="w-3 h-3 text-amber-500" />
                <span>Grafana</span>
              </a>
            )}

            {/* Tema Değiştirici */}
            <ThemeToggle />

            {/* Kullanıcı Oturum Bilgileri */}
            {isLoggedIn ? (
              <div className="flex items-center gap-2 sm:gap-3">
                {/* Bakiye Rozeti */}
                {balance !== null && (
                  <div className="flex items-center gap-1.5 bg-emerald-50 dark:bg-emerald-950/40 border border-emerald-200 dark:border-emerald-800/60 px-3 py-1.5 rounded-full text-xs shadow-sm">
                    <Wallet className="w-3.5 h-3.5 text-emerald-600 dark:text-emerald-400 shrink-0" />
                    <span className="font-bold text-emerald-700 dark:text-emerald-300">
                      ${balance.toFixed(2)}
                    </span>
                  </div>
                )}

                {/* Admin Rozeti */}
                {userRole === "admin" && (
                  <span className="hidden sm:inline-flex items-center gap-1 text-[11px] font-bold text-purple-700 dark:text-purple-300 bg-purple-50 dark:bg-purple-950/60 border border-purple-200 dark:border-purple-800 px-2.5 py-1 rounded-lg">
                    <ShieldAlert className="w-3 h-3 text-purple-600 dark:text-purple-400" /> Admin
                  </span>
                )}

                {/* Kullanıcı E-Postası */}
                {userEmail && (
                  <span className="hidden xl:inline-block text-xs text-slate-600 dark:text-gray-400 font-mono bg-slate-100 dark:bg-gray-900/60 px-2.5 py-1 rounded-lg border border-slate-200 dark:border-gray-800 max-w-[180px] truncate">
                    {userEmail}
                  </span>
                )}

                {/* Çıkış Yap Butonu */}
                <button
                  onClick={handleLogout}
                  title="Güvenli Çıkış Yap"
                  className="flex items-center gap-1 px-2.5 py-1.5 rounded-xl text-xs text-slate-600 dark:text-gray-400 hover:text-red-600 dark:hover:text-red-400 hover:bg-red-50 dark:hover:bg-red-950/30 transition border border-slate-200 dark:border-gray-800 font-semibold"
                >
                  <LogOut className="w-3.5 h-3.5" />
                  <span className="hidden sm:inline">Çıkış</span>
                </button>
              </div>
            ) : (
              <div className="flex items-center gap-2">
                <span className="text-xs text-slate-500 dark:text-gray-400 font-medium hidden sm:inline">
                  Kurumsal AI Ağ Geçidi
                </span>
              </div>
            )}

          </div>

        </div>
      </div>
    </header>
  );
}
