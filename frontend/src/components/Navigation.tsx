"use client";

import React, { useState, useEffect, useRef } from "react";
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
  RefreshCw,
  ChevronDown,
  Key,
  Layers,
  CheckCircle2,
  ExternalLink,
  CreditCard,
  Download
} from "lucide-react";
import { getAuthToken, clearAuthToken, fetchApi } from "../lib/api";
import ThemeToggle from "./ThemeToggle";

export default function Navigation() {
  const pathname = usePathname();
  const router = useRouter();
  const [balance, setBalance] = useState<number | null>(null);
  const [userProfile, setUserProfile] = useState<any | null>(null);
  const [isLoggedIn, setIsLoggedIn] = useState<boolean>(false);
  const [isDropdownOpen, setIsDropdownOpen] = useState<boolean>(false);
  const dropdownRef = useRef<HTMLDivElement>(null);

  const loadUserState = async () => {
    const token = getAuthToken();
    if (!token) {
      setIsLoggedIn(false);
      setBalance(null);
      setUserProfile(null);
      return;
    }
    setIsLoggedIn(true);
    try {
      const walletData = await fetchApi("/api/wallet");
      if (walletData && walletData.balance_usd !== undefined) {
        setBalance(Number(walletData.balance_usd));
      }
      const profile = await fetchApi("/api/auth/me");
      if (profile) {
        setUserProfile(profile);
      }
    } catch (err) {
      console.error("Failed to load user info:", err);
    }
  };

  useEffect(() => {
    loadUserState();
  }, [pathname]);

  // Click outside to close dropdown
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target as Node)) {
        setIsDropdownOpen(false);
      }
    };
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

  const handleLogout = () => {
    clearAuthToken();
    setIsLoggedIn(false);
    setBalance(null);
    setUserProfile(null);
    setIsDropdownOpen(false);
    router.push("/");
    window.location.reload();
  };

  const isAdmin = Boolean(
    userProfile?.role?.toLowerCase() === "admin" ||
    userProfile?.email?.toLowerCase() === "admin@bedrockgateway.com" ||
    userProfile?.role === "ADMIN"
  );

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

          {/* Sağ Bölüm: Tema & Profil Açılır Menüsü */}
          <div className="flex items-center gap-2 sm:gap-3 shrink-0">
            
            {/* Tema Değiştirici */}
            <ThemeToggle />

            {/* Giriş Yapmış Kullanıcı Açılır Profil Menüsü */}
            {isLoggedIn ? (
              <div className="relative" ref={dropdownRef}>
                {/* Profil Tetikleyici Buton */}
                <button
                  type="button"
                  onClick={() => setIsDropdownOpen(!isDropdownOpen)}
                  className="flex items-center gap-2 pl-2 pr-3 py-1.5 rounded-2xl border border-slate-200 dark:border-gray-800 bg-slate-50 dark:bg-gray-900/80 hover:border-indigo-500 dark:hover:border-indigo-500 transition shadow-sm group"
                >
                  {/* Avatar Görseli veya Harf */}
                  <div className="w-7 h-7 rounded-xl bg-gradient-to-tr from-indigo-600 to-purple-600 flex items-center justify-center text-white font-bold text-xs shadow-sm overflow-hidden shrink-0">
                    {userProfile?.avatar_url ? (
                      <img src={userProfile.avatar_url} alt="Avatar" className="w-full h-full object-cover" />
                    ) : (
                      <span>{userProfile?.full_name?.charAt(0)?.toUpperCase() || userProfile?.email?.charAt(0)?.toUpperCase() || "U"}</span>
                    )}
                  </div>

                  {/* Bakiye & İsim Özeti */}
                  <div className="hidden sm:flex flex-col text-left">
                    <span className="text-[11px] font-bold text-slate-800 dark:text-gray-200 max-w-[120px] truncate">
                      {userProfile?.full_name || userProfile?.email?.split("@")[0]}
                    </span>
                    <span className="text-[10px] font-extrabold text-emerald-600 dark:text-emerald-400 font-mono">
                      ${balance !== null ? balance.toFixed(2) : "0.00"} USD
                    </span>
                  </div>

                  <ChevronDown className={`w-3.5 h-3.5 text-slate-400 group-hover:text-indigo-600 transition transform ${isDropdownOpen ? "rotate-180" : ""}`} />
                </button>

                {/* Açılır Profil & Yönetim Popover Menüsü */}
                {isDropdownOpen && (
                  <div className="absolute right-0 mt-2 w-72 rounded-3xl bg-white dark:bg-gray-900 border border-slate-200 dark:border-gray-800 shadow-2xl z-50 p-2 space-y-2 animate-in fade-in slide-in-from-top-2 duration-150">
                    
                    {/* Üst Kullanıcı Bilgi Kartı */}
                    <div className="p-3.5 rounded-2xl bg-gradient-to-br from-indigo-50 to-purple-50 dark:from-indigo-950/40 dark:to-purple-950/30 border border-indigo-100 dark:border-indigo-900/50 space-y-1.5">
                      <div className="flex items-center justify-between">
                        <span className="text-xs font-black text-slate-900 dark:text-white truncate max-w-[160px]">
                          {userProfile?.full_name || userProfile?.email}
                        </span>
                        <span className="px-2 py-0.5 rounded text-[9px] font-black uppercase tracking-wide bg-indigo-600 text-white">
                          {userProfile?.role || "USER"}
                        </span>
                      </div>
                      <div className="text-[11px] text-slate-500 dark:text-gray-400 font-mono truncate">
                        {userProfile?.email}
                      </div>
                      <div className="pt-1.5 flex items-center justify-between border-t border-indigo-200/40 dark:border-indigo-900/40 text-xs">
                        <span className="text-slate-500 dark:text-gray-400 font-semibold">Cüzdan:</span>
                        <strong className="text-emerald-600 dark:text-emerald-400 font-black">
                          ${balance !== null ? balance.toFixed(2) : "0.00"} USD
                        </strong>
                      </div>
                    </div>

                    {/* Menü Linkleri */}
                    <div className="space-y-0.5 text-xs font-semibold text-slate-700 dark:text-gray-300">
                      <Link
                        href="/"
                        onClick={() => setIsDropdownOpen(false)}
                        className="flex items-center gap-2.5 px-3 py-2 rounded-xl hover:bg-slate-100 dark:hover:bg-gray-800 transition"
                      >
                        <UserIcon className="w-4 h-4 text-indigo-600" />
                        <span>Profil & Cüzdan Yönetimi</span>
                      </Link>

                      <Link
                        href="/"
                        onClick={() => setIsDropdownOpen(false)}
                        className="flex items-center gap-2.5 px-3 py-2 rounded-xl hover:bg-slate-100 dark:hover:bg-gray-800 transition"
                      >
                        <Key className="w-4 h-4 text-emerald-500" />
                        <span>Geliştirici & API Merkezi</span>
                      </Link>

                      <Link
                        href="/"
                        onClick={() => setIsDropdownOpen(false)}
                        className="flex items-center gap-2.5 px-3 py-2 rounded-xl hover:bg-slate-100 dark:hover:bg-gray-800 transition"
                      >
                        <Cpu className="w-4 h-4 text-purple-500" />
                        <span>Model Kataloğu</span>
                      </Link>

                      {isAdmin && (
                        <>
                          <div className="my-1 border-t border-slate-100 dark:border-gray-800" />
                          <Link
                            href="/"
                            onClick={() => setIsDropdownOpen(false)}
                            className="flex items-center gap-2.5 px-3 py-2 rounded-xl bg-purple-50/60 dark:bg-purple-950/30 text-purple-700 dark:text-purple-300 hover:bg-purple-100/60 transition"
                          >
                            <ShieldAlert className="w-4 h-4 text-purple-600" />
                            <span>Admin & AWS Konsolu</span>
                          </Link>

                          <a
                            href="http://bedrock-gateway-alb-664380835.us-east-1.elb.amazonaws.com:3001"
                            target="_blank"
                            rel="noreferrer"
                            onClick={() => setIsDropdownOpen(false)}
                            className="flex items-center justify-between px-3 py-2 rounded-xl text-amber-600 dark:text-amber-400 hover:bg-amber-50 dark:hover:bg-amber-950/30 transition"
                          >
                            <div className="flex items-center gap-2.5">
                              <Activity className="w-4 h-4 text-amber-500" />
                              <span>Grafana Canlı Panel</span>
                            </div>
                            <ExternalLink className="w-3.5 h-3.5" />
                          </a>
                        </>
                      )}
                    </div>

                    {/* Çıkış Yap */}
                    <div className="pt-1 border-t border-slate-100 dark:border-gray-800">
                      <button
                        type="button"
                        onClick={handleLogout}
                        className="w-full flex items-center gap-2 px-3 py-2 rounded-xl text-red-600 dark:text-red-400 hover:bg-red-50 dark:hover:bg-red-950/30 text-xs font-bold transition"
                      >
                        <LogOut className="w-4 h-4" />
                        <span>Güvenli Çıkış Yap</span>
                      </button>
                    </div>

                  </div>
                )}
              </div>
            ) : (
              <Link
                href="/"
                className="px-4 py-2 rounded-xl bg-indigo-600 hover:bg-indigo-500 text-white font-bold text-xs shadow-md shadow-indigo-600/20 transition"
              >
                Giriş Yap
              </Link>
            )}

          </div>

        </div>
      </div>
    </header>
  );
}
