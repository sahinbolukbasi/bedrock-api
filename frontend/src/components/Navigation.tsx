"use client";

import React, { useState, useEffect } from "react";
import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { 
  LogOut, 
  Wallet,
  User as UserIcon,
  ShieldAlert
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

  useEffect(() => {
    async function loadUserState() {
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
        setBalance(Number(walletData.balance_usd));
        const userProfile = await fetchApi("/api/auth/me");
        setUserEmail(userProfile.email || null);
        setUserRole(userProfile.role || "user");
      } catch (err) {
        console.error("Failed to load user info:", err);
      }
    }
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
    <nav className="border-b border-slate-200 dark:border-gray-800/80 bg-white/90 dark:bg-[#0b0f17]/90 backdrop-blur-md sticky top-0 z-50 transition-colors">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-16">
          
          {/* Logo */}
          <div className="flex items-center gap-3">
            <Link href="/" className="flex items-center gap-2.5 group">
              <div className="w-8 h-8 rounded-xl bg-gradient-to-tr from-indigo-500 via-purple-500 to-amber-500 p-[2px] shadow-sm">
                <div className="w-full h-full bg-white dark:bg-gray-950 rounded-[10px] flex items-center justify-center font-black text-slate-900 dark:text-white text-xs">
                  BG
                </div>
              </div>
              <div>
                <span className="font-bold text-sm text-slate-900 dark:text-white tracking-tight group-hover:text-indigo-600 dark:group-hover:text-indigo-400 transition">
                  Bedrock<span className="text-amber-500">Gateway</span>
                </span>
                <span className="ml-1.5 px-1.5 py-0.5 text-[9px] font-semibold bg-indigo-50 dark:bg-indigo-950 text-indigo-700 dark:text-indigo-300 border border-indigo-200 dark:border-indigo-800 rounded">
                  AWS Multi-Model
                </span>
              </div>
            </Link>
          </div>

          {/* Right Action Bar */}
          <div className="flex items-center gap-3">
            
            {/* Dark / Light Theme Toggle Switch */}
            <ThemeToggle />

            {/* If Logged In: Show Balance, Role Badge & User controls */}
            {isLoggedIn && (
              <>
                {balance !== null && (
                  <div className="hidden sm:flex items-center gap-2 bg-slate-100 dark:bg-gray-900/80 border border-slate-200 dark:border-gray-800 px-3 py-1.5 rounded-full text-xs shadow-sm">
                    <Wallet className="w-3.5 h-3.5 text-emerald-600 dark:text-emerald-400" />
                    <span className="text-slate-700 dark:text-gray-300 font-medium">
                      Bakiye: <strong className="text-emerald-600 dark:text-emerald-400 font-black">${balance.toFixed(2)}</strong>
                    </span>
                  </div>
                )}

                {userRole === "admin" && (
                  <span className="hidden md:inline-flex items-center gap-1 text-[11px] font-bold text-purple-700 dark:text-purple-300 bg-purple-50 dark:bg-purple-950/60 border border-purple-200 dark:border-purple-800 px-2.5 py-1 rounded-lg">
                    <ShieldAlert className="w-3 h-3 text-purple-600 dark:text-purple-400" /> Admin
                  </span>
                )}

                {userEmail && (
                  <span className="hidden lg:inline-block text-xs text-slate-600 dark:text-gray-400 font-mono bg-slate-100 dark:bg-gray-900/60 px-2.5 py-1 rounded-lg border border-slate-200 dark:border-gray-800">
                    {userEmail}
                  </span>
                )}

                <button
                  onClick={handleLogout}
                  title="Çıkış Yap"
                  className="flex items-center gap-1.5 px-3 py-1.5 rounded-xl text-xs text-slate-600 dark:text-gray-400 hover:text-red-600 dark:hover:text-red-400 hover:bg-slate-100 dark:hover:bg-gray-900 transition border border-transparent hover:border-slate-200 dark:hover:border-gray-800 font-medium"
                >
                  <LogOut className="w-3.5 h-3.5" />
                  <span className="hidden sm:inline">Çıkış</span>
                </button>
              </>
            )}

          </div>

        </div>
      </div>
    </nav>
  );
}
