"use client";

import React, { useState, useEffect } from "react";
import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { 
  LogOut, 
  Wallet,
  PlusCircle
} from "lucide-react";
import { getAuthToken, clearAuthToken, fetchApi } from "../lib/api";
import ThemeToggle from "./ThemeToggle";

export default function Navigation() {
  const pathname = usePathname();
  const router = useRouter();
  const [balance, setBalance] = useState<number | null>(null);
  const [userEmail, setUserEmail] = useState<string | null>(null);
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
    <nav className="border-b border-gray-800/80 dark:border-gray-800/80 light:border-slate-200 bg-gray-950/90 dark:bg-[#0b0f17]/90 light:bg-white/90 backdrop-blur-md sticky top-0 z-50 transition-colors">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-16">
          
          {/* Logo (Clean & Minimalist) */}
          <div className="flex items-center gap-3">
            <Link href="/" className="flex items-center gap-2.5 group">
              <div className="w-8 h-8 rounded-xl bg-gradient-to-tr from-indigo-500 via-purple-500 to-amber-500 p-[2px] shadow-sm">
                <div className="w-full h-full bg-gray-950 dark:bg-gray-950 light:bg-white rounded-[10px] flex items-center justify-center font-black text-white light:text-slate-900 text-xs">
                  BG
                </div>
              </div>
              <span className="font-bold text-sm text-white light:text-slate-900 tracking-tight group-hover:text-indigo-400 transition">
                Bedrock<span className="text-amber-500">Gateway</span>
              </span>
            </Link>
          </div>

          {/* Right Action Bar */}
          <div className="flex items-center gap-3">
            
            {/* Dark / Light Theme Toggle Switch */}
            <ThemeToggle />

            {/* If Logged In: Show Balance & User controls */}
            {isLoggedIn && (
              <>
                {balance !== null && (
                  <div className="hidden sm:flex items-center gap-2 bg-gray-900/80 dark:bg-gray-900/80 light:bg-slate-100 border border-gray-800 dark:border-gray-800 light:border-slate-200 px-3 py-1 rounded-full text-xs">
                    <Wallet className="w-3.5 h-3.5 text-emerald-400" />
                    <span className="text-gray-300 light:text-slate-700">
                      Balance: <strong className="text-emerald-400">${balance.toFixed(2)}</strong>
                    </span>
                  </div>
                )}

                {userEmail && (
                  <span className="hidden md:inline-block text-xs text-gray-400 light:text-slate-500 font-mono bg-gray-900/60 dark:bg-gray-900/60 light:bg-slate-100 px-2 py-1 rounded border border-gray-800 dark:border-gray-800 light:border-slate-200">
                    {userEmail}
                  </span>
                )}

                <button
                  onClick={handleLogout}
                  title="Sign Out"
                  className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs text-gray-400 hover:text-red-400 hover:bg-gray-900 light:hover:bg-slate-100 transition border border-transparent hover:border-gray-800 dark:hover:border-gray-800 light:hover:border-slate-200"
                >
                  <LogOut className="w-3.5 h-3.5" />
                  <span className="hidden sm:inline">Sign Out</span>
                </button>
              </>
            )}

          </div>

        </div>
      </div>
    </nav>
  );
}
