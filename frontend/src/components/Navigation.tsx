"use client";

import React, { useState, useEffect } from "react";
import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { 
  MessageSquare, 
  Cpu, 
  Key, 
  BarChart3, 
  CreditCard, 
  BookOpen, 
  ShieldAlert, 
  LogOut, 
  Wallet,
  PlusCircle,
  Menu,
  X
} from "lucide-react";
import { getAuthToken, clearAuthToken, fetchApi } from "../lib/api";

export default function Navigation() {
  const pathname = usePathname();
  const router = useRouter();
  const [balance, setBalance] = useState<number | null>(null);
  const [userRole, setUserRole] = useState<string>("user");
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);

  useEffect(() => {
    async function loadWallet() {
      const token = getAuthToken();
      if (!token) return;
      try {
        const walletData = await fetchApi("/api/wallet");
        setBalance(Number(walletData.balance_usd));
        const userProfile = await fetchApi("/api/auth/me");
        setUserRole(userProfile.role || "user");
      } catch (err) {
        console.error("Failed to load user info:", err);
      }
    }
    loadWallet();
  }, [pathname]);

  const handleLogout = () => {
    clearAuthToken();
    router.push("/login");
  };

  const navItems = [
    { name: "Chat Playground", href: "/chat", icon: MessageSquare },
    { name: "Models", href: "/models", icon: Cpu },
    { name: "API Keys", href: "/api-keys", icon: Key },
    { name: "Usage & Analytics", href: "/usage", icon: BarChart3 },
    { name: "Billing & Credits", href: "/billing", icon: CreditCard },
    { name: "API Docs", href: "/docs", icon: BookOpen },
  ];

  if (userRole === "admin") {
    navItems.push({ name: "Admin Console", href: "/admin", icon: ShieldAlert });
  }

  // Hide nav on login/register pages
  if (pathname === "/login" || pathname === "/register") {
    return null;
  }

  return (
    <nav className="border-b border-gray-800 bg-gray-950/80 backdrop-blur-md sticky top-0 z-50">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-16">
          
          {/* Logo */}
          <div className="flex items-center gap-3">
            <Link href="/" className="flex items-center gap-2 group">
              <div className="w-9 h-9 rounded-lg bg-gradient-to-tr from-indigo-500 via-purple-500 to-amber-500 p-[2px]">
                <div className="w-full h-full bg-gray-950 rounded-[7px] flex items-center justify-center font-black text-white text-sm">
                  BG
                </div>
              </div>
              <div>
                <span className="font-bold text-base text-white tracking-tight group-hover:text-indigo-400 transition">
                  Bedrock<span className="text-amber-500">Gateway</span>
                </span>
                <span className="ml-1.5 px-1.5 py-0.5 text-[10px] font-semibold bg-indigo-950 text-indigo-300 border border-indigo-800 rounded">
                  v1.0
                </span>
              </div>
            </Link>

            {/* Desktop Navigation Links */}
            <div className="hidden md:flex items-center ml-8 space-x-1">
              {navItems.map((item) => {
                const Icon = item.icon;
                const isActive = pathname === item.href;
                return (
                  <Link
                    key={item.name}
                    href={item.href}
                    className={`flex items-center gap-2 px-3 py-2 rounded-lg text-xs font-medium transition ${
                      isActive
                        ? "bg-indigo-600/20 text-indigo-400 border border-indigo-500/30"
                        : "text-gray-400 hover:text-gray-200 hover:bg-gray-900"
                    }`}
                  >
                    <Icon className="w-4 h-4" />
                    {item.name}
                  </Link>
                );
              })}
            </div>
          </div>

          {/* Right Action Bar */}
          <div className="hidden md:flex items-center gap-4">
            {balance !== null ? (
              <div className="flex items-center gap-2 bg-gray-900 border border-gray-800 px-3 py-1.5 rounded-full">
                <Wallet className="w-3.5 h-3.5 text-emerald-400" />
                <span className="text-xs font-medium text-gray-300">
                  Balance: <strong className="text-emerald-400">${balance.toFixed(2)}</strong>
                </span>
                <Link
                  href="/billing"
                  className="text-[11px] font-semibold text-indigo-400 hover:text-indigo-300 flex items-center gap-0.5 ml-1"
                >
                  <PlusCircle className="w-3 h-3" /> Add
                </Link>
              </div>
            ) : (
              <Link
                href="/login"
                className="text-xs text-indigo-400 hover:text-indigo-300 font-medium"
              >
                Sign In
              </Link>
            )}

            {balance !== null && (
              <button
                onClick={handleLogout}
                title="Sign Out"
                className="p-2 rounded-lg text-gray-400 hover:text-red-400 hover:bg-gray-900 transition"
              >
                <LogOut className="w-4 h-4" />
              </button>
            )}
          </div>

          {/* Mobile Menu Button */}
          <div className="flex md:hidden">
            <button
              onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
              className="text-gray-400 hover:text-white p-2"
            >
              {mobileMenuOpen ? <X className="w-6 h-6" /> : <Menu className="w-6 h-6" />}
            </button>
          </div>

        </div>
      </div>

      {/* Mobile Menu Dropdown */}
      {mobileMenuOpen && (
        <div className="md:hidden border-b border-gray-800 bg-gray-950 px-4 pt-2 pb-4 space-y-1">
          {navItems.map((item) => {
            const Icon = item.icon;
            const isActive = pathname === item.href;
            return (
              <Link
                key={item.name}
                href={item.href}
                onClick={() => setMobileMenuOpen(false)}
                className={`flex items-center gap-3 px-3 py-2 rounded-lg text-sm font-medium ${
                  isActive
                    ? "bg-indigo-600/20 text-indigo-400 border border-indigo-500/30"
                    : "text-gray-400 hover:text-gray-200"
                }`}
              >
                <Icon className="w-4 h-4" />
                {item.name}
              </Link>
            );
          })}
          {balance !== null && (
            <button
              onClick={handleLogout}
              className="flex items-center gap-3 w-full text-left px-3 py-2 rounded-lg text-sm font-medium text-red-400 hover:bg-gray-900"
            >
              <LogOut className="w-4 h-4" /> Sign Out
            </button>
          )}
        </div>
      )}
    </nav>
  );
}
