"use client";

import React, { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { 
  MessageSquare, 
  Cpu, 
  Key, 
  BarChart3, 
  CreditCard, 
  ShieldAlert, 
  Lock, 
  Mail, 
  ArrowRight, 
  Sparkles, 
  Layers,
  CheckCircle2,
  AlertCircle,
  Coins,
  Activity,
  Send,
  Plus,
  Trash2,
  Copy,
  Check,
  Zap,
  DollarSign,
  Users
} from "lucide-react";
import { API_BASE, getAuthToken, setAuthToken, fetchApi, clearAuthToken } from "../lib/api";
import { useTheme } from "../components/ThemeProvider";

export default function RootPage() {
  const router = useRouter();
  const { theme, toggleTheme } = useTheme();
  
  // Auth state
  const [token, setToken] = useState<string | null>(null);
  const [user, setUser] = useState<any | null>(null);
  const [loading, setLoading] = useState<boolean>(true);

  // Guest Login Form state
  const [loginEmail, setLoginEmail] = useState("admin@bedrockgateway.com");
  const [loginPassword, setLoginPassword] = useState("AdminPassword123!");
  const [loginError, setLoginError] = useState("");
  const [loginLoading, setLoginLoading] = useState(false);

  // Console Hub Active Tab state
  const [activeTab, setActiveTab] = useState<"chat" | "keys" | "models" | "usage" | "billing" | "admin">("chat");

  // Console data states
  const [models, setModels] = useState<any[]>([]);
  const [balance, setBalance] = useState<number>(0);
  const [apiKeys, setApiKeys] = useState<any[]>([]);
  const [usageSummary, setUsageSummary] = useState<any>(null);
  const [adminOverview, setAdminOverview] = useState<any>(null);

  // Chat playground state
  const [messages, setMessages] = useState<any[]>([
    {
      id: "1",
      role: "assistant",
      content: "Hello! Connected to **AWS Bedrock**. Choose a foundation model from above and start chatting or streaming inference.",
    },
  ]);
  const [chatInput, setChatInput] = useState("");
  const [selectedModel, setSelectedModel] = useState("anthropic.claude-3-5-sonnet-20241022-v2:0");
  const [isStreaming, setIsStreaming] = useState(false);

  // Check auth on load
  useEffect(() => {
    async function checkAuth() {
      const savedToken = getAuthToken();
      if (!savedToken) {
        setToken(null);
        setUser(null);
        setLoading(false);
        return;
      }
      setToken(savedToken);
      try {
        const userProfile = await fetchApi("/api/auth/me");
        setUser(userProfile);
        const walletData = await fetchApi("/api/wallet");
        setBalance(Number(walletData.balance_usd));
        const modelsData = await fetchApi("/v1/models");
        setModels(modelsData.data || []);
      } catch (err) {
        console.error("Auth check failed:", err);
        clearAuthToken();
        setToken(null);
      } finally {
        setLoading(false);
      }
    }
    checkAuth();
  }, []);

  // Handle Guest Sign In
  const handleLoginSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoginError("");
    setLoginLoading(true);

    try {
      const res = await fetch(`${API_BASE}/api/auth/login`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email: loginEmail, password: loginPassword }),
      });

      const data = await res.json();
      if (!res.ok) {
        throw new Error(data?.detail || "Invalid email or password");
      }

      setAuthToken(data.access_token);
      setToken(data.access_token);
      setUser({ email: data.email, role: data.role, id: data.user_id });
      
      // Load console data
      const walletData = await fetchApi("/api/wallet");
      setBalance(Number(walletData.balance_usd));
      const modelsData = await fetchApi("/v1/models");
      setModels(modelsData.data || []);
    } catch (err: any) {
      setLoginError(err.message || "Failed to connect to gateway");
    } finally {
      setLoginLoading(false);
    }
  };

  // Switch tabs & fetch module data
  const handleTabChange = async (tab: any) => {
    setActiveTab(tab);
    if (tab === "keys") {
      try {
        const data = await fetchApi("/api/keys");
        setApiKeys(data || []);
      } catch {}
    } else if (tab === "usage") {
      try {
        const data = await fetchApi("/api/usage/summary");
        setUsageSummary(data);
      } catch {}
    } else if (tab === "admin") {
      try {
        const data = await fetchApi("/api/admin/overview");
        setAdminOverview(data);
      } catch {}
    }
  };

  // Chat send message
  const handleSendMessage = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!chatInput.trim() || isStreaming) return;

    const userMsg = { id: Date.now().toString(), role: "user", content: chatInput };
    const assistantMsg = { id: (Date.now() + 1).toString(), role: "assistant", content: "" };
    
    setMessages((prev) => [...prev, userMsg, assistantMsg]);
    setChatInput("");
    setIsStreaming(true);

    try {
      const response = await fetch(`${API_BASE}/v1/chat/completions`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify({
          model: selectedModel,
          messages: [...messages, userMsg].map((m) => ({ role: m.role, content: m.content })),
          stream: true,
        }),
      });

      if (!response.ok) {
        throw new Error(`API Error: ${response.status}`);
      }

      const reader = response.body?.getReader();
      const decoder = new TextDecoder();
      let fullText = "";

      if (reader) {
        while (true) {
          const { done, value } = await reader.read();
          if (done) break;
          const chunk = decoder.decode(value);
          const lines = chunk.split("\n");
          for (const line of lines) {
            if (line.startsWith("data: ") && line !== "data: [DONE]") {
              try {
                const parsed = JSON.parse(line.slice(6));
                const content = parsed.choices[0]?.delta?.content || "";
                fullText += content;
                setMessages((prev) => {
                  const updated = [...prev];
                  updated[updated.length - 1].content = fullText;
                  return updated;
                });
              } catch {}
            }
          }
        }
      }
    } catch (err: any) {
      setMessages((prev) => {
        const updated = [...prev];
        updated[updated.length - 1].content = `⚠️ Error: ${err.message || "Failed to generate response"}`;
        return updated;
      });
    } finally {
      setIsStreaming(false);
      // Refresh wallet balance
      fetchApi("/api/wallet").then((w) => setBalance(Number(w.balance_usd))).catch(() => {});
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-950 text-white">
        <div className="w-8 h-8 border-4 border-indigo-500 border-t-transparent rounded-full animate-spin" />
      </div>
    );
  }

  // =========================================================================
  // LAYER 1: GUEST ENTRANCE GATEWAY (ZERO DISTRACTING BUTTONS)
  // =========================================================================
  if (!token) {
    return (
      <div className="min-h-[calc(100vh-64px)] flex items-center justify-center p-4 relative overflow-hidden bg-slate-950 dark:bg-[#0b0f17] light:bg-[#f8fafc]">
        {/* Ambient Glow */}
        <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[500px] h-[500px] bg-indigo-500/10 dark:bg-indigo-500/20 blur-[130px] pointer-events-none rounded-full" />

        <div className="w-full max-w-md relative z-10">
          <div className="rounded-3xl border border-gray-800/80 bg-gray-900/90 dark:bg-gray-900/90 light:bg-white light:border-slate-200 shadow-2xl p-8 backdrop-blur-xl">
            
            {/* Logo & Header */}
            <div className="text-center mb-8">
              <div className="w-12 h-12 mx-auto rounded-2xl bg-gradient-to-tr from-indigo-500 via-purple-500 to-amber-500 p-[2px] mb-4 shadow-lg shadow-indigo-500/20">
                <div className="w-full h-full bg-gray-950 dark:bg-gray-950 light:bg-white rounded-[14px] flex items-center justify-center font-black text-white light:text-slate-900 text-lg">
                  BG
                </div>
              </div>
              <h1 className="text-2xl font-bold text-white light:text-slate-900 tracking-tight">
                Bedrock <span className="text-amber-400">Gateway</span>
              </h1>
              <p className="text-xs text-gray-400 light:text-slate-500 mt-1.5">
                Unified AI Control Center & Management Console
              </p>
            </div>

            {/* Error Alert */}
            {loginError && (
              <div className="mb-6 p-3 rounded-xl bg-red-500/10 border border-red-500/30 flex items-center gap-2 text-xs text-red-400">
                <AlertCircle className="w-4 h-4 flex-shrink-0" />
                <span>{loginError}</span>
              </div>
            )}

            {/* Direct Login Form */}
            <form onSubmit={handleLoginSubmit} className="space-y-4">
              <div>
                <label className="block text-xs font-semibold text-gray-300 light:text-slate-700 mb-1.5">
                  Email Address
                </label>
                <div className="relative">
                  <Mail className="w-4 h-4 text-gray-500 absolute left-3.5 top-3" />
                  <input
                    type="email"
                    required
                    value={loginEmail}
                    onChange={(e) => setLoginEmail(e.target.value)}
                    placeholder="admin@bedrockgateway.com"
                    className="w-full bg-gray-950/80 dark:bg-gray-950/80 light:bg-slate-50 border border-gray-800 dark:border-gray-800 light:border-slate-200 rounded-xl pl-10 pr-4 py-2.5 text-xs text-white light:text-slate-900 focus:outline-none focus:border-indigo-500 transition"
                  />
                </div>
              </div>

              <div>
                <label className="block text-xs font-semibold text-gray-300 light:text-slate-700 mb-1.5">
                  Password
                </label>
                <div className="relative">
                  <Lock className="w-4 h-4 text-gray-500 absolute left-3.5 top-3" />
                  <input
                    type="password"
                    required
                    value={loginPassword}
                    onChange={(e) => setLoginPassword(e.target.value)}
                    placeholder="••••••••••••"
                    className="w-full bg-gray-950/80 dark:bg-gray-950/80 light:bg-slate-50 border border-gray-800 dark:border-gray-800 light:border-slate-200 rounded-xl pl-10 pr-4 py-2.5 text-xs text-white light:text-slate-900 focus:outline-none focus:border-indigo-500 transition"
                  />
                </div>
              </div>

              <button
                type="submit"
                disabled={loginLoading}
                className="w-full mt-2 py-3 rounded-xl bg-indigo-600 hover:bg-indigo-500 text-white font-bold text-xs transition shadow-lg shadow-indigo-600/30 flex items-center justify-center gap-2 disabled:opacity-50"
              >
                {loginLoading ? (
                  <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
                ) : (
                  <>
                    <span>Enter Management Console</span>
                    <ArrowRight className="w-4 h-4" />
                  </>
                )}
              </button>
            </form>

            <div className="mt-6 pt-4 border-t border-gray-800/80 dark:border-gray-800 light:border-slate-200 text-center text-[11px] text-gray-500 light:text-slate-400">
              Default Admin: <code className="text-indigo-400 font-mono">admin@bedrockgateway.com</code>
            </div>

          </div>
        </div>
      </div>
    );
  }

  // =========================================================================
  // LAYER 2: UNIFIED CONSOLE & ALL-IN-ONE ADMIN WORKSPACE HUB
  // =========================================================================
  return (
    <div className="min-h-[calc(100vh-64px)] flex flex-col md:flex-row bg-slate-950 dark:bg-[#0b0f17] light:bg-[#f8fafc]">
      
      {/* Left Workspace Navigation Sidebar */}
      <aside className="w-full md:w-64 border-r border-gray-800/80 dark:border-gray-800 light:border-slate-200 bg-gray-950/50 dark:bg-gray-950/50 light:bg-white p-4 flex flex-col justify-between">
        <div className="space-y-6">
          
          {/* Quick Balance Header Card */}
          <div className="p-3.5 rounded-2xl bg-gray-900/80 dark:bg-gray-900/80 light:bg-slate-50 border border-gray-800 dark:border-gray-800 light:border-slate-200">
            <div className="flex items-center justify-between text-xs text-gray-400 light:text-slate-500 mb-1">
              <span>Account Balance</span>
              <Coins className="w-3.5 h-3.5 text-amber-400" />
            </div>
            <div className="text-xl font-black text-emerald-400 light:text-emerald-600">
              ${balance.toFixed(2)}
            </div>
            <div className="mt-2 text-[10px] text-gray-500 light:text-slate-400 truncate">
              {user?.email} ({user?.role})
            </div>
          </div>

          {/* Module Nav Links */}
          <nav className="space-y-1">
            <button
              onClick={() => handleTabChange("chat")}
              className={`w-full flex items-center gap-3 px-3.5 py-2.5 rounded-xl text-xs font-semibold transition ${
                activeTab === "chat"
                  ? "bg-indigo-600 text-white shadow-md shadow-indigo-600/20"
                  : "text-gray-400 light:text-slate-600 hover:text-white light:hover:text-slate-900 hover:bg-gray-900 light:hover:bg-slate-100"
              }`}
            >
              <MessageSquare className="w-4 h-4" />
              <span>Chat Playground</span>
            </button>

            <button
              onClick={() => handleTabChange("keys")}
              className={`w-full flex items-center gap-3 px-3.5 py-2.5 rounded-xl text-xs font-semibold transition ${
                activeTab === "keys"
                  ? "bg-indigo-600 text-white shadow-md shadow-indigo-600/20"
                  : "text-gray-400 light:text-slate-600 hover:text-white light:hover:text-slate-900 hover:bg-gray-900 light:hover:bg-slate-100"
              }`}
            >
              <Key className="w-4 h-4" />
              <span>API Keys Manager</span>
            </button>

            <button
              onClick={() => handleTabChange("models")}
              className={`w-full flex items-center gap-3 px-3.5 py-2.5 rounded-xl text-xs font-semibold transition ${
                activeTab === "models"
                  ? "bg-indigo-600 text-white shadow-md shadow-indigo-600/20"
                  : "text-gray-400 light:text-slate-600 hover:text-white light:hover:text-slate-900 hover:bg-gray-900 light:hover:bg-slate-100"
              }`}
            >
              <Cpu className="w-4 h-4" />
              <span>Models Catalog</span>
            </button>

            <button
              onClick={() => handleTabChange("usage")}
              className={`w-full flex items-center gap-3 px-3.5 py-2.5 rounded-xl text-xs font-semibold transition ${
                activeTab === "usage"
                  ? "bg-indigo-600 text-white shadow-md shadow-indigo-600/20"
                  : "text-gray-400 light:text-slate-600 hover:text-white light:hover:text-slate-900 hover:bg-gray-900 light:hover:bg-slate-100"
              }`}
            >
              <BarChart3 className="w-4 h-4" />
              <span>Usage & Metrics</span>
            </button>

            <button
              onClick={() => handleTabChange("billing")}
              className={`w-full flex items-center gap-3 px-3.5 py-2.5 rounded-xl text-xs font-semibold transition ${
                activeTab === "billing"
                  ? "bg-indigo-600 text-white shadow-md shadow-indigo-600/20"
                  : "text-gray-400 light:text-slate-600 hover:text-white light:hover:text-slate-900 hover:bg-gray-900 light:hover:bg-slate-100"
              }`}
            >
              <CreditCard className="w-4 h-4" />
              <span>Billing & Top-Up</span>
            </button>

            {user?.role === "admin" && (
              <button
                onClick={() => handleTabChange("admin")}
                className={`w-full flex items-center gap-3 px-3.5 py-2.5 rounded-xl text-xs font-semibold transition ${
                  activeTab === "admin"
                    ? "bg-purple-600 text-white shadow-md shadow-purple-600/20"
                    : "text-purple-400 light:text-purple-600 hover:bg-purple-950/30 light:hover:bg-purple-50"
                }`}
              >
                <ShieldAlert className="w-4 h-4" />
                <span>Admin Controls</span>
              </button>
            )}
          </nav>
        </div>

        {/* Sidebar Footer Controls */}
        <div className="pt-4 border-t border-gray-800/80 dark:border-gray-800 light:border-slate-200 flex items-center justify-between">
          <button
            onClick={() => {
              clearAuthToken();
              setToken(null);
              setUser(null);
            }}
            className="text-xs text-red-400 hover:text-red-300 font-medium"
          >
            Log Out
          </button>
          <span className="text-[10px] text-gray-500">v1.0 Production</span>
        </div>
      </aside>

      {/* Main Interactive Workspace Area */}
      <main className="flex-1 p-4 md:p-6 overflow-y-auto">
        
        {/* TAB 1: CHAT PLAYGROUND */}
        {activeTab === "chat" && (
          <div className="max-w-4xl mx-auto flex flex-col h-[calc(100vh-140px)]">
            <div className="flex items-center justify-between mb-4 bg-gray-900/60 dark:bg-gray-900/60 light:bg-white border border-gray-800 dark:border-gray-800 light:border-slate-200 p-3 rounded-2xl">
              <div className="flex items-center gap-2">
                <Sparkles className="w-4 h-4 text-indigo-400" />
                <span className="text-xs font-bold text-white light:text-slate-900">Bedrock Model:</span>
                <select
                  value={selectedModel}
                  onChange={(e) => setSelectedModel(e.target.value)}
                  className="bg-gray-950 dark:bg-gray-950 light:bg-slate-50 border border-gray-800 dark:border-gray-800 light:border-slate-200 rounded-lg px-3 py-1.5 text-xs text-indigo-300 light:text-indigo-600 focus:outline-none"
                >
                  <option value="anthropic.claude-3-5-sonnet-20241022-v2:0">Claude 3.5 Sonnet v2</option>
                  <option value="anthropic.claude-3-5-haiku-20241022-v1:0">Claude 3.5 Haiku</option>
                  <option value="amazon.nova-pro-v1:0">Amazon Nova Pro</option>
                  <option value="amazon.nova-lite-v1:0">Amazon Nova Lite</option>
                  <option value="meta.llama3-3-70b-instruct-v1:0">Meta Llama 3.3 70B</option>
                </select>
              </div>
              <span className="text-[11px] text-emerald-400 font-mono">SSE Real-Time Active</span>
            </div>

            {/* Chat Messages */}
            <div className="flex-1 overflow-y-auto space-y-4 p-4 rounded-2xl bg-gray-900/40 dark:bg-gray-900/40 light:bg-white border border-gray-800 dark:border-gray-800 light:border-slate-200 mb-4">
              {messages.map((m) => (
                <div
                  key={m.id}
                  className={`flex gap-3 text-xs leading-relaxed ${
                    m.role === "user" ? "justify-end" : "justify-start"
                  }`}
                >
                  <div
                    className={`max-w-[80%] rounded-2xl p-4 ${
                      m.role === "user"
                        ? "bg-indigo-600 text-white font-medium"
                        : "bg-gray-950 dark:bg-gray-950 light:bg-slate-100 text-gray-200 light:text-slate-800 border border-gray-800 dark:border-gray-800 light:border-slate-200"
                    }`}
                  >
                    <div className="text-[10px] opacity-60 mb-1 uppercase font-bold tracking-wider">
                      {m.role === "user" ? "You" : selectedModel.split(".")[1] || "AI Assistant"}
                    </div>
                    <div className="whitespace-pre-wrap">{m.content}</div>
                  </div>
                </div>
              ))}
            </div>

            {/* Chat Input */}
            <form onSubmit={handleSendMessage} className="flex gap-2">
              <input
                type="text"
                value={chatInput}
                onChange={(e) => setChatInput(e.target.value)}
                placeholder="Ask AWS Bedrock anything or test prompts..."
                className="flex-1 bg-gray-900/90 dark:bg-gray-900/90 light:bg-white border border-gray-800 dark:border-gray-800 light:border-slate-200 rounded-xl px-4 py-3 text-xs text-white light:text-slate-900 focus:outline-none focus:border-indigo-500 transition"
              />
              <button
                type="submit"
                disabled={isStreaming || !chatInput.trim()}
                className="px-6 rounded-xl bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-bold transition flex items-center gap-1.5 disabled:opacity-40"
              >
                <Send className="w-4 h-4" />
                <span>Send</span>
              </button>
            </form>
          </div>
        )}

        {/* TAB 2: API KEYS */}
        {activeTab === "keys" && (
          <div className="max-w-4xl mx-auto space-y-6">
            <div className="flex items-center justify-between">
              <div>
                <h2 className="text-xl font-bold text-white light:text-slate-900">API Keys Manager</h2>
                <p className="text-xs text-gray-400 light:text-slate-500 mt-0.5">
                  Generate scoped API keys for OpenAI SDK and HTTP client integrations.
                </p>
              </div>
              <Link
                href="/api-keys"
                className="px-4 py-2 rounded-xl bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-bold transition flex items-center gap-1.5"
              >
                <Plus className="w-4 h-4" /> Create New Key
              </Link>
            </div>

            <div className="p-6 rounded-2xl bg-gray-900/40 dark:bg-gray-900/40 light:bg-white border border-gray-800 dark:border-gray-800 light:border-slate-200">
              <div className="flex items-center gap-2 mb-4 text-xs font-bold text-gray-300 light:text-slate-700">
                <Key className="w-4 h-4 text-indigo-400" />
                <span>Active OpenAI Base URL</span>
              </div>
              <div className="bg-gray-950 dark:bg-gray-950 light:bg-slate-100 p-3 rounded-xl border border-gray-800 dark:border-gray-800 light:border-slate-200 font-mono text-xs text-indigo-400 break-all">
                http://bedrock-gateway-alb-664380835.us-east-1.elb.amazonaws.com:8000/v1
              </div>
            </div>
          </div>
        )}

        {/* TAB 3: MODELS CATALOG */}
        {activeTab === "models" && (
          <div className="max-w-5xl mx-auto space-y-6">
            <h2 className="text-xl font-bold text-white light:text-slate-900">Supported Foundation Models</h2>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {models.map((m) => (
                <div
                  key={m.id}
                  className="p-5 rounded-2xl bg-gray-900/50 dark:bg-gray-900/50 light:bg-white border border-gray-800 dark:border-gray-800 light:border-slate-200"
                >
                  <div className="flex items-center justify-between mb-2">
                    <span className="font-bold text-sm text-white light:text-slate-900">{m.name}</span>
                    <span className="text-[10px] px-2 py-0.5 rounded bg-indigo-950 text-indigo-300 border border-indigo-800">
                      {m.type}
                    </span>
                  </div>
                  <div className="text-xs text-gray-400 font-mono mb-3">{m.id}</div>
                  <div className="text-[11px] text-gray-400 light:text-slate-500 flex justify-between pt-2 border-t border-gray-800/60 dark:border-gray-800/60 light:border-slate-100">
                    <span>Context: {m.context_window?.toLocaleString()} tokens</span>
                    <span className="text-emerald-400 font-semibold">
                      ${m.pricing?.input_per_1k}/1k In · ${m.pricing?.output_per_1k}/1k Out
                    </span>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* TAB 4: USAGE */}
        {activeTab === "usage" && (
          <div className="max-w-4xl mx-auto space-y-6">
            <h2 className="text-xl font-bold text-white light:text-slate-900">Usage & Cost Analytics</h2>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div className="p-5 rounded-2xl bg-gray-900/40 dark:bg-gray-900/40 light:bg-white border border-gray-800 dark:border-gray-800 light:border-slate-200">
                <div className="text-xs text-gray-400">Total Spend (USD)</div>
                <div className="text-2xl font-black text-white light:text-slate-900 mt-1">
                  ${usageSummary?.total_spent_usd?.toFixed(4) || "0.0000"}
                </div>
              </div>
              <div className="p-5 rounded-2xl bg-gray-900/40 dark:bg-gray-900/40 light:bg-white border border-gray-800 dark:border-gray-800 light:border-slate-200">
                <div className="text-xs text-gray-400">Total Invocations</div>
                <div className="text-2xl font-black text-indigo-400 mt-1">
                  {usageSummary?.total_requests || 0}
                </div>
              </div>
              <div className="p-5 rounded-2xl bg-gray-900/40 dark:bg-gray-900/40 light:bg-white border border-gray-800 dark:border-gray-800 light:border-slate-200">
                <div className="text-xs text-gray-400">Total Tokens</div>
                <div className="text-2xl font-black text-emerald-400 mt-1">
                  {usageSummary?.total_tokens?.toLocaleString() || 0}
                </div>
              </div>
            </div>
          </div>
        )}

        {/* TAB 5: BILLING */}
        {activeTab === "billing" && (
          <div className="max-w-4xl mx-auto space-y-6">
            <h2 className="text-xl font-bold text-white light:text-slate-900">Wallet & Credits Top-Up</h2>
            <div className="p-6 rounded-3xl bg-gradient-to-r from-indigo-950/60 to-purple-950/60 border border-indigo-800/50 flex items-center justify-between">
              <div>
                <span className="text-xs text-indigo-300 font-medium">Available Balance</span>
                <div className="text-3xl font-black text-white mt-1">${balance.toFixed(2)} USD</div>
              </div>
              <Link
                href="/billing"
                className="px-6 py-3 rounded-xl bg-indigo-600 hover:bg-indigo-500 text-white font-bold text-xs shadow-lg shadow-indigo-600/30 transition"
              >
                Top-Up via Stripe
              </Link>
            </div>
          </div>
        )}

        {/* TAB 6: ADMIN */}
        {activeTab === "admin" && (
          <div className="max-w-5xl mx-auto space-y-6">
            <h2 className="text-xl font-bold text-white light:text-slate-900">System Admin Control Center</h2>
            <div className="p-6 rounded-2xl bg-gray-900/40 dark:bg-gray-900/40 light:bg-white border border-gray-800 dark:border-gray-800 light:border-slate-200">
              <div className="text-sm font-bold text-purple-400 mb-2">Platform Overview</div>
              <div className="text-xs text-gray-400 light:text-slate-600">
                Multi-AZ Fargate Cluster · PostgreSQL Row-Lock Wallet · Redis Rate Limiter · AWS WAF Active
              </div>
            </div>
          </div>
        )}

      </main>
    </div>
  );
}
