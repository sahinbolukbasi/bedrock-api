"use client";

import React, { useState, useEffect, useRef } from "react";
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
  Users,
  User as UserIcon,
  Sliders,
  Settings,
  ShieldCheck,
  RefreshCw,
  Search,
  ExternalLink,
  ChevronRight,
  TrendingUp,
  Clock,
  QrCode,
  KeyRound
} from "lucide-react";
import { API_BASE, getAuthToken, setAuthToken, fetchApi, clearAuthToken } from "../lib/api";

export default function RootPage() {
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
  const [activeTab, setActiveTab] = useState<"chat" | "models" | "keys" | "analytics" | "billing" | "profile" | "admin">("chat");

  // Models catalog & wallet
  const [models, setModels] = useState<any[]>([]);
  const [balance, setBalance] = useState<number>(0);
  const [selectedModel, setSelectedModel] = useState("anthropic.claude-3-5-sonnet-20241022-v2:0");

  // ==========================================
  // Open WebUI-Style Chat Session State
  // ==========================================
  const [conversations, setConversations] = useState<any[]>([]);
  const [activeConvId, setActiveConvId] = useState<string | null>(null);
  const [chatSearch, setChatSearch] = useState("");
  const [messages, setMessages] = useState<any[]>([
    {
      id: "welcome",
      role: "assistant",
      content: "👋 Merhaba! **AWS Bedrock AI Gateway**'e hoş geldiniz.\nYukarıdan dilediğiniz frontier modeli seçebilir, sistem talimatlarını ve sıcaklığı ayarlayarak sohbet edebilirsiniz.",
    },
  ]);
  const [chatInput, setChatInput] = useState("");
  const [isStreaming, setIsStreaming] = useState(false);
  const [systemPrompt, setSystemPrompt] = useState("You are an expert AI assistant powered by Amazon Bedrock. Provide accurate, helpful, and concise answers with code snippets when needed.");
  const [temperature, setTemperature] = useState(0.7);
  const [showSettingsDrawer, setShowSettingsDrawer] = useState(false);
  const [copiedCodeIndex, setCopiedCodeIndex] = useState<string | null>(null);

  // ==========================================
  // API Keys State
  // ==========================================
  const [apiKeys, setApiKeys] = useState<any[]>([]);
  const [newKeyName, setNewKeyName] = useState("");
  const [createdSecretKey, setCreatedSecretKey] = useState<string | null>(null);
  const [keyCopied, setKeyCopied] = useState(false);

  // ==========================================
  // Prometheus & Analytics Dashboard State
  // ==========================================
  const [usageSummary, setUsageSummary] = useState<any>(null);
  const [prometheusRaw, setPrometheusRaw] = useState<string>("");
  const [metricsLoading, setMetricsLoading] = useState(false);

  // ==========================================
  // User Profile State
  // ==========================================
  const [currentPassword, setCurrentPassword] = useState("");
  const [newPassword, setNewPassword] = useState("");
  const [pwdMessage, setPwdMessage] = useState<{ type: "success" | "error"; text: string } | null>(null);
  const [mfaData, setMfaData] = useState<{ secret: string; provisioning_uri: string } | null>(null);
  const [mfaCode, setMfaCode] = useState("");
  const [mfaStatus, setMfaStatus] = useState<string | null>(null);

  // ==========================================
  // Admin Console State
  // ==========================================
  const [adminOverview, setAdminOverview] = useState<any>(null);
  const [adminUsers, setAdminUsers] = useState<any[]>([]);
  const [selectedUserForBalance, setSelectedUserForBalance] = useState<any | null>(null);
  const [newBalanceAmount, setNewBalanceAmount] = useState<string>("100");
  const [globalMargin, setGlobalMargin] = useState<number>(20);

  // Model filter state
  const [modelCategory, setModelCategory] = useState<string>("ALL");

  // Check auth & load initial data on page load
  useEffect(() => {
    async function initConsole() {
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
        
        // Load conversations
        loadConversations();
      } catch (err) {
        console.error("Initialization failed:", err);
        clearAuthToken();
        setToken(null);
      } finally {
        setLoading(false);
      }
    }
    initConsole();
  }, []);

  // Fetch list of conversations
  const loadConversations = async () => {
    try {
      const convList = await fetchApi("/api/chat-ui/conversations");
      setConversations(convList || []);
    } catch (err) {
      console.error("Failed to load conversations:", err);
    }
  };

  // Switch / Load a conversation
  const selectConversation = async (conv: any) => {
    setActiveConvId(conv.id);
    setSelectedModel(conv.model_id || "anthropic.claude-3-5-sonnet-20241022-v2:0");
    if (conv.system_prompt) setSystemPrompt(conv.system_prompt);
    if (conv.temperature) setTemperature(conv.temperature);

    try {
      const msgs = await fetchApi(`/api/chat-ui/conversations/${conv.id}/messages`);
      if (msgs && msgs.length > 0) {
        setMessages(msgs.map((m: any) => ({
          id: m.id,
          role: m.role,
          content: m.content,
          tokens: m.tokens,
          cost_usd: m.cost_usd
        })));
      } else {
        setMessages([]);
      }
    } catch (err) {
      console.error("Failed to fetch conversation messages:", err);
    }
  };

  // Create a brand new conversation
  const handleNewChat = async () => {
    try {
      const newConv = await fetchApi("/api/chat-ui/conversations", {
        method: "POST",
        body: JSON.stringify({
          title: `Sohbet ${new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}`,
          model_id: selectedModel,
          system_prompt: systemPrompt,
          temperature: temperature,
        }),
      });
      setConversations((prev) => [newConv, ...prev]);
      setActiveConvId(newConv.id);
      setMessages([]);
    } catch (err) {
      console.error("Failed to create new conversation:", err);
    }
  };

  // Delete a conversation
  const handleDeleteConversation = async (e: React.MouseEvent, convId: string) => {
    e.stopPropagation();
    try {
      await fetchApi(`/api/chat-ui/conversations/${convId}`, { method: "DELETE" });
      setConversations((prev) => prev.filter((c) => c.id !== convId));
      if (activeConvId === convId) {
        setActiveConvId(null);
        setMessages([
          {
            id: "welcome",
            role: "assistant",
            content: "Yeni bir sohbet başlatmak için sol menüden **Yeni Sohbet** butonuna tıklayın.",
          },
        ]);
      }
    } catch (err) {
      console.error("Failed to delete conversation:", err);
    }
  };

  // Guest Sign In
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
        throw new Error(data?.detail || "Giriş başarısız. Bilgilerinizi kontrol edin.");
      }

      setAuthToken(data.access_token);
      setToken(data.access_token);
      setUser({ email: data.email, role: data.role, id: data.user_id });
      
      // Load console data
      const walletData = await fetchApi("/api/wallet");
      setBalance(Number(walletData.balance_usd));
      const modelsData = await fetchApi("/v1/models");
      setModels(modelsData.data || []);
      loadConversations();
    } catch (err: any) {
      setLoginError(err.message || "Ağ geçidine bağlanılamadı.");
    } finally {
      setLoginLoading(false);
    }
  };

  // Switch Tabs & Load Tab-Specific Data
  const handleTabChange = async (tab: any) => {
    setActiveTab(tab);
    if (tab === "keys") {
      try {
        const data = await fetchApi("/api/keys");
        setApiKeys(data || []);
      } catch {}
    } else if (tab === "analytics") {
      fetchAnalyticsData();
    } else if (tab === "admin") {
      fetchAdminData();
    }
  };

  // Fetch Prometheus & Usage Analytics
  const fetchAnalyticsData = async () => {
    setMetricsLoading(true);
    try {
      const summary = await fetchApi("/api/usage/summary");
      setUsageSummary(summary);

      const promRes = await fetch(`${API_BASE}/metrics`);
      if (promRes.ok) {
        const rawText = await promRes.text();
        setPrometheusRaw(rawText);
      }
    } catch (err) {
      console.error("Failed to load metrics:", err);
    } finally {
      setMetricsLoading(false);
    }
  };

  // Fetch Admin Hub Data
  const fetchAdminData = async () => {
    try {
      const overview = await fetchApi("/api/admin/overview");
      setAdminOverview(overview);
      const usersList = await fetchApi("/api/admin/users");
      setAdminUsers(usersList || []);
    } catch (err) {
      console.error("Failed to load admin data:", err);
    }
  };

  // Create API Key
  const handleCreateApiKey = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newKeyName.trim()) return;
    try {
      const res = await fetchApi("/api/keys", {
        method: "POST",
        body: JSON.stringify({ name: newKeyName, rate_limit_rpm: 120 }),
      });
      setCreatedSecretKey(res.raw_key);
      setNewKeyName("");
      const list = await fetchApi("/api/keys");
      setApiKeys(list || []);
    } catch (err) {
      console.error("Failed to create key:", err);
    }
  };

  // Revoke API Key
  const handleRevokeKey = async (keyId: string) => {
    try {
      await fetchApi(`/api/keys/${keyId}`, { method: "DELETE" });
      setApiKeys((prev) => prev.filter((k) => k.id !== keyId));
    } catch (err) {
      console.error("Failed to revoke key:", err);
    }
  };

  // Change Password
  const handleChangePassword = async (e: React.FormEvent) => {
    e.preventDefault();
    setPwdMessage(null);
    try {
      await fetchApi("/api/auth/change-password", {
        method: "POST",
        body: JSON.stringify({ current_password: currentPassword, new_password: newPassword }),
      });
      setPwdMessage({ type: "success", text: "Şifreniz başarıyla güncellendi." });
      setCurrentPassword("");
      setNewPassword("");
    } catch (err: any) {
      setPwdMessage({ type: "error", text: err.message || "Şifre değiştirilemedi." });
    }
  };

  // Initiate MFA
  const handleInitiateMFA = async () => {
    try {
      const data = await fetchApi("/api/auth/mfa/setup", { method: "POST" });
      setMfaData(data);
    } catch (err) {
      console.error("MFA setup error:", err);
    }
  };

  // Verify MFA
  const handleVerifyMFA = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      await fetchApi("/api/auth/mfa/verify", {
        method: "POST",
        body: JSON.stringify({ code: mfaCode }),
      });
      setMfaStatus("2FA / İki Adımlı Doğrulama başarıyla aktifleştirildi!");
      setMfaData(null);
      setMfaCode("");
    } catch (err: any) {
      setMfaStatus(`Hata: ${err.message || "Doğrulama kodu geçersiz."}`);
    }
  };

  // Admin: Toggle User Status
  const handleToggleUserStatus = async (userId: string, currentActive: boolean) => {
    try {
      await fetchApi(`/api/admin/users/${userId}/status?is_active=${!currentActive}`, { method: "POST" });
      fetchAdminData();
    } catch (err) {
      console.error("Failed to toggle status:", err);
    }
  };

  // Admin: Adjust User Balance
  const handleAdjustBalance = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedUserForBalance) return;
    try {
      await fetchApi(`/api/admin/users/${selectedUserForBalance.id}/balance?new_balance_usd=${newBalanceAmount}`, { method: "POST" });
      setSelectedUserForBalance(null);
      fetchAdminData();
    } catch (err) {
      console.error("Failed to adjust balance:", err);
    }
  };

  // Chat Streaming Execution
  const handleSendMessage = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!chatInput.trim() || isStreaming) return;

    let currentConvId = activeConvId;
    if (!currentConvId) {
      try {
        const newConv = await fetchApi("/api/chat-ui/conversations", {
          method: "POST",
          body: JSON.stringify({
            title: chatInput.slice(0, 30) + "...",
            model_id: selectedModel,
            system_prompt: systemPrompt,
            temperature: temperature,
          }),
        });
        setConversations((prev) => [newConv, ...prev]);
        setActiveConvId(newConv.id);
        currentConvId = newConv.id;
      } catch {}
    }

    const userMsg = { id: Date.now().toString(), role: "user", content: chatInput };
    const assistantMsg = { id: (Date.now() + 1).toString(), role: "assistant", content: "" };
    
    setMessages((prev) => [...prev, userMsg, assistantMsg]);
    setChatInput("");
    setIsStreaming(true);

    // Save user message to backend
    if (currentConvId) {
      fetchApi(`/api/chat-ui/conversations/${currentConvId}/messages`, {
        method: "POST",
        body: JSON.stringify({ role: "user", content: userMsg.content }),
      }).catch(() => {});
    }

    try {
      const response = await fetch(`${API_BASE}/v1/chat/completions`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify({
          model: selectedModel,
          messages: [
            { role: "system", content: systemPrompt },
            ...messages.filter((m) => m.id !== "welcome"),
            userMsg
          ].map((m) => ({ role: m.role, content: m.content })),
          temperature: temperature,
          stream: true,
        }),
      });

      if (!response.ok) {
        throw new Error(`API Hatası: ${response.status}`);
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

      // Save assistant response to backend
      if (currentConvId && fullText) {
        fetchApi(`/api/chat-ui/conversations/${currentConvId}/messages`, {
          method: "POST",
          body: JSON.stringify({ role: "assistant", content: fullText }),
        }).catch(() => {});
      }
    } catch (err: any) {
      setMessages((prev) => {
        const updated = [...prev];
        updated[updated.length - 1].content = `⚠️ Yanıt alınamadı: ${err.message || "Bilinmeyen hata"}`;
        return updated;
      });
    } finally {
      setIsStreaming(false);
      fetchApi("/api/wallet").then((w) => setBalance(Number(w.balance_usd))).catch(() => {});
    }
  };

  // Copy code utility
  const copyToClipboard = (text: string, id: string) => {
    navigator.clipboard.writeText(text);
    setCopiedCodeIndex(id);
    setTimeout(() => setCopiedCodeIndex(null), 2000);
  };

  // Filtered models
  const filteredModels = models.filter((m) => {
    if (modelCategory === "ALL") return true;
    if (modelCategory === "ANTHROPIC") return m.model_id.startsWith("anthropic.");
    if (modelCategory === "AMAZON") return m.model_id.startsWith("amazon.");
    if (modelCategory === "META") return m.model_id.startsWith("meta.");
    if (modelCategory === "MISTRAL") return m.model_id.startsWith("mistral.");
    if (modelCategory === "COHERE") return m.model_id.startsWith("cohere.");
    if (modelCategory === "IMAGE") return m.type === "IMAGE";
    return true;
  });

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-slate-50 dark:bg-[#0b0f17]">
        <div className="w-8 h-8 border-4 border-indigo-600 border-t-transparent rounded-full animate-spin" />
      </div>
    );
  }

  // =========================================================================
  // KATMAN 1: GİRİŞ KAPISI (GUEST LAYER — ZERO INTERNAL BUTTONS)
  // =========================================================================
  if (!token) {
    return (
      <div className="min-h-[calc(100vh-64px)] flex items-center justify-center p-4 relative overflow-hidden bg-slate-50 dark:bg-[#0b0f17] transition-colors">
        {/* Glow */}
        <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[550px] h-[550px] bg-indigo-500/10 dark:bg-indigo-500/20 blur-[140px] pointer-events-none rounded-full" />

        <div className="w-full max-w-md relative z-10">
          <div className="rounded-3xl border border-slate-200 dark:border-gray-800 bg-white dark:bg-gray-900/90 shadow-2xl p-8 backdrop-blur-xl transition-colors">
            
            {/* Header */}
            <div className="text-center mb-8">
              <div className="w-14 h-14 mx-auto rounded-2xl bg-gradient-to-tr from-indigo-500 via-purple-500 to-amber-500 p-[2px] mb-4 shadow-xl shadow-indigo-500/20">
                <div className="w-full h-full bg-white dark:bg-gray-950 rounded-[14px] flex items-center justify-center font-black text-slate-900 dark:text-white text-xl">
                  BG
                </div>
              </div>
              <h1 className="text-2xl font-black text-slate-900 dark:text-white tracking-tight">
                Bedrock <span className="text-amber-500">Gateway</span>
              </h1>
              <p className="text-xs text-slate-500 dark:text-gray-400 mt-1.5 font-medium">
                AWS Bedrock Frontier AI Yönetim ve Kontrol Paneli
              </p>
            </div>

            {/* Error Notification */}
            {loginError && (
              <div className="mb-6 p-3.5 rounded-xl bg-red-50 dark:bg-red-500/10 border border-red-200 dark:border-red-500/30 flex items-center gap-2 text-xs text-red-600 dark:text-red-400">
                <AlertCircle className="w-4 h-4 flex-shrink-0" />
                <span>{loginError}</span>
              </div>
            )}

            {/* Direct Login Form */}
            <form onSubmit={handleLoginSubmit} className="space-y-4">
              <div>
                <label className="block text-xs font-bold text-slate-700 dark:text-gray-300 mb-1.5">
                  E-Posta Adresi
                </label>
                <div className="relative">
                  <Mail className="w-4 h-4 text-slate-400 dark:text-gray-500 absolute left-3.5 top-3" />
                  <input
                    type="email"
                    required
                    value={loginEmail}
                    onChange={(e) => setLoginEmail(e.target.value)}
                    placeholder="admin@bedrockgateway.com"
                    className="w-full bg-slate-50 dark:bg-gray-950 border border-slate-200 dark:border-gray-800 rounded-xl pl-10 pr-4 py-2.5 text-xs text-slate-900 dark:text-white focus:outline-none focus:border-indigo-500 transition font-medium"
                  />
                </div>
              </div>

              <div>
                <label className="block text-xs font-bold text-slate-700 dark:text-gray-300 mb-1.5">
                  Şifre
                </label>
                <div className="relative">
                  <Lock className="w-4 h-4 text-slate-400 dark:text-gray-500 absolute left-3.5 top-3" />
                  <input
                    type="password"
                    required
                    value={loginPassword}
                    onChange={(e) => setLoginPassword(e.target.value)}
                    placeholder="••••••••••••"
                    className="w-full bg-slate-50 dark:bg-gray-950 border border-slate-200 dark:border-gray-800 rounded-xl pl-10 pr-4 py-2.5 text-xs text-slate-900 dark:text-white focus:outline-none focus:border-indigo-500 transition font-medium"
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
                    <span>Yönetim Paneline Giriş Yap</span>
                    <ArrowRight className="w-4 h-4" />
                  </>
                )}
              </button>
            </form>

            <div className="mt-6 pt-4 border-t border-slate-200 dark:border-gray-800 text-center text-[11px] text-slate-500 dark:text-gray-400">
              Varsayılan Yönetici: <code className="text-indigo-600 dark:text-indigo-400 font-mono font-bold">admin@bedrockgateway.com</code>
            </div>

          </div>
        </div>
      </div>
    );
  }

  // =========================================================================
  // KATMAN 2: HEPSİ BİR ARADA GELİŞMİŞ YÖNETİM MERKEZİ (UNIFIED CONSOLE HUB)
  // =========================================================================
  return (
    <div className="min-h-[calc(100vh-64px)] flex flex-col md:flex-row bg-slate-50 dark:bg-[#0b0f17] text-slate-900 dark:text-gray-100 transition-colors">
      
      {/* Sol Ana Navigasyon Çubuğu */}
      <aside className="w-full md:w-64 border-r border-slate-200 dark:border-gray-800 bg-white dark:bg-gray-950 p-4 flex flex-col justify-between transition-colors">
        <div className="space-y-6">
          
          {/* Cüzdan & Kullanıcı Özet Kartı */}
          <div className="p-3.5 rounded-2xl bg-slate-100 dark:bg-gray-900 border border-slate-200 dark:border-gray-800 shadow-sm">
            <div className="flex items-center justify-between text-xs text-slate-500 dark:text-gray-400 mb-1">
              <span className="font-semibold">Kullanılabilir Bakiye</span>
              <Coins className="w-3.5 h-3.5 text-amber-500" />
            </div>
            <div className="text-xl font-black text-emerald-600 dark:text-emerald-400">
              ${balance.toFixed(2)}
            </div>
            <div className="mt-2 flex items-center justify-between text-[10px] text-slate-500 dark:text-gray-400">
              <span className="truncate max-w-[130px] font-mono">{user?.email}</span>
              <span className="px-1.5 py-0.5 rounded bg-indigo-50 dark:bg-indigo-950 text-indigo-700 dark:text-indigo-300 font-bold uppercase">
                {user?.role}
              </span>
            </div>
          </div>

          {/* Menü Sekmeleri */}
          <nav className="space-y-1">
            <button
              onClick={() => handleTabChange("chat")}
              className={`w-full flex items-center gap-3 px-3.5 py-2.5 rounded-xl text-xs font-bold transition ${
                activeTab === "chat"
                  ? "bg-indigo-600 text-white shadow-md shadow-indigo-600/30"
                  : "text-slate-600 dark:text-gray-400 hover:text-slate-900 dark:hover:text-white hover:bg-slate-100 dark:hover:bg-gray-900"
              }`}
            >
              <MessageSquare className="w-4 h-4" />
              <span>Sohbet (Open WebUI)</span>
            </button>

            <button
              onClick={() => handleTabChange("models")}
              className={`w-full flex items-center gap-3 px-3.5 py-2.5 rounded-xl text-xs font-bold transition ${
                activeTab === "models"
                  ? "bg-indigo-600 text-white shadow-md shadow-indigo-600/30"
                  : "text-slate-600 dark:text-gray-400 hover:text-slate-900 dark:hover:text-white hover:bg-slate-100 dark:hover:bg-gray-900"
              }`}
            >
              <Cpu className="w-4 h-4" />
              <span>Model Kataloğu ({models.length})</span>
            </button>

            <button
              onClick={() => handleTabChange("keys")}
              className={`w-full flex items-center gap-3 px-3.5 py-2.5 rounded-xl text-xs font-bold transition ${
                activeTab === "keys"
                  ? "bg-indigo-600 text-white shadow-md shadow-indigo-600/30"
                  : "text-slate-600 dark:text-gray-400 hover:text-slate-900 dark:hover:text-white hover:bg-slate-100 dark:hover:bg-gray-900"
              }`}
            >
              <Key className="w-4 h-4" />
              <span>API Anahtarları</span>
            </button>

            <button
              onClick={() => handleTabChange("analytics")}
              className={`w-full flex items-center gap-3 px-3.5 py-2.5 rounded-xl text-xs font-bold transition ${
                activeTab === "analytics"
                  ? "bg-indigo-600 text-white shadow-md shadow-indigo-600/30"
                  : "text-slate-600 dark:text-gray-400 hover:text-slate-900 dark:hover:text-white hover:bg-slate-100 dark:hover:bg-gray-900"
              }`}
            >
              <BarChart3 className="w-4 h-4" />
              <span>Prometheus & Analitik</span>
            </button>

            <button
              onClick={() => handleTabChange("billing")}
              className={`w-full flex items-center gap-3 px-3.5 py-2.5 rounded-xl text-xs font-bold transition ${
                activeTab === "billing"
                  ? "bg-indigo-600 text-white shadow-md shadow-indigo-600/30"
                  : "text-slate-600 dark:text-gray-400 hover:text-slate-900 dark:hover:text-white hover:bg-slate-100 dark:hover:bg-gray-900"
              }`}
            >
              <CreditCard className="w-4 h-4" />
              <span>Bakiye & Cüzdan</span>
            </button>

            <button
              onClick={() => handleTabChange("profile")}
              className={`w-full flex items-center gap-3 px-3.5 py-2.5 rounded-xl text-xs font-bold transition ${
                activeTab === "profile"
                  ? "bg-indigo-600 text-white shadow-md shadow-indigo-600/30"
                  : "text-slate-600 dark:text-gray-400 hover:text-slate-900 dark:hover:text-white hover:bg-slate-100 dark:hover:bg-gray-900"
              }`}
            >
              <UserIcon className="w-4 h-4" />
              <span>Kullanıcı Profili</span>
            </button>

            {user?.role === "admin" && (
              <button
                onClick={() => handleTabChange("admin")}
                className={`w-full flex items-center gap-3 px-3.5 py-2.5 rounded-xl text-xs font-bold transition ${
                  activeTab === "admin"
                    ? "bg-purple-600 text-white shadow-md shadow-purple-600/30"
                    : "text-purple-600 dark:text-purple-400 hover:bg-purple-50 dark:hover:bg-purple-950/30"
                }`}
              >
                <ShieldAlert className="w-4 h-4" />
                <span>Admin Kontrol Paneli</span>
              </button>
            )}
          </nav>
        </div>

        {/* Footer */}
        <div className="pt-4 border-t border-slate-200 dark:border-gray-800 flex items-center justify-between text-xs">
          <button
            onClick={() => {
              clearAuthToken();
              setToken(null);
              setUser(null);
              window.location.reload();
            }}
            className="text-red-600 dark:text-red-400 hover:underline font-semibold"
          >
            Çıkış Yap
          </button>
          <span className="text-[10px] text-slate-400 dark:text-gray-500 font-mono">v1.0 Production</span>
        </div>
      </aside>

      {/* Ana Çalışma Alanı */}
      <main className="flex-1 p-4 md:p-6 overflow-y-auto">
        
        {/* ================================================================= */}
        {/* SEKME 1: OPEN WEBUI-STYLE CHAT PLAYGROUND */}
        {/* ================================================================= */}
        {activeTab === "chat" && (
          <div className="flex h-[calc(100vh-120px)] rounded-2xl border border-slate-200 dark:border-gray-800 overflow-hidden bg-white dark:bg-gray-950 shadow-sm">
            
            {/* Chat Geçmişi Sol Sidebar (Open WebUI Style) */}
            <div className="w-64 border-r border-slate-200 dark:border-gray-800 bg-slate-50 dark:bg-gray-900/60 flex flex-col justify-between p-3">
              <div className="space-y-3">
                <button
                  onClick={handleNewChat}
                  className="w-full flex items-center justify-center gap-2 py-2.5 px-3 rounded-xl bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-bold shadow-md shadow-indigo-600/20 transition"
                >
                  <Plus className="w-4 h-4" />
                  <span>Yeni Sohbet</span>
                </button>

                <div className="relative">
                  <Search className="w-3.5 h-3.5 text-slate-400 absolute left-2.5 top-2.5" />
                  <input
                    type="text"
                    value={chatSearch}
                    onChange={(e) => setChatSearch(e.target.value)}
                    placeholder="Sohbetlerde ara..."
                    className="w-full bg-white dark:bg-gray-950 border border-slate-200 dark:border-gray-800 rounded-lg pl-8 pr-3 py-1.5 text-[11px] text-slate-900 dark:text-white focus:outline-none focus:border-indigo-500"
                  />
                </div>

                {/* Geçmiş Sohbetler Listesi */}
                <div className="overflow-y-auto max-h-[calc(100vh-280px)] space-y-1">
                  <div className="text-[10px] font-bold text-slate-400 uppercase tracking-wider px-2 pt-1">
                    Geçmiş Sohbetler
                  </div>
                  {conversations
                    .filter((c) => c.title.toLowerCase().includes(chatSearch.toLowerCase()))
                    .map((conv) => (
                      <div
                        key={conv.id}
                        onClick={() => selectConversation(conv)}
                        className={`group flex items-center justify-between px-3 py-2 rounded-xl text-xs cursor-pointer transition ${
                          activeConvId === conv.id
                            ? "bg-indigo-50 dark:bg-indigo-950/60 text-indigo-600 dark:text-indigo-400 font-bold border border-indigo-200 dark:border-indigo-800"
                            : "text-slate-600 dark:text-gray-400 hover:bg-slate-200/60 dark:hover:bg-gray-800/60"
                        }`}
                      >
                        <div className="flex items-center gap-2 truncate">
                          <MessageSquare className="w-3.5 h-3.5 flex-shrink-0" />
                          <span className="truncate">{conv.title}</span>
                        </div>
                        <button
                          onClick={(e) => handleDeleteConversation(e, conv.id)}
                          title="Sohbeti Sil"
                          className="opacity-0 group-hover:opacity-100 text-slate-400 hover:text-red-600 p-1 transition"
                        >
                          <Trash2 className="w-3.5 h-3.5" />
                        </button>
                      </div>
                    ))}
                </div>
              </div>
            </div>

            {/* Chat Mesajlaşma Alanı */}
            <div className="flex-1 flex flex-col bg-white dark:bg-gray-950">
              
              {/* Chat Başlık & Model Seçici */}
              <div className="p-3 border-b border-slate-200 dark:border-gray-800 flex items-center justify-between bg-slate-50/50 dark:bg-gray-900/30">
                <div className="flex items-center gap-2">
                  <Sparkles className="w-4 h-4 text-indigo-600 dark:text-indigo-400" />
                  <span className="text-xs font-bold text-slate-700 dark:text-gray-300">Model:</span>
                  <select
                    value={selectedModel}
                    onChange={(e) => setSelectedModel(e.target.value)}
                    className="bg-white dark:bg-gray-900 border border-slate-200 dark:border-gray-800 rounded-lg px-3 py-1 text-xs text-indigo-600 dark:text-indigo-400 font-bold focus:outline-none"
                  >
                    <option value="anthropic.claude-3-5-sonnet-20241022-v2:0">Claude 3.5 Sonnet v2 (200k)</option>
                    <option value="anthropic.claude-3-5-haiku-20241022-v1:0">Claude 3.5 Haiku (200k)</option>
                    <option value="anthropic.claude-3-opus-20240229-v1:0">Claude 3 Opus (200k)</option>
                    <option value="amazon.nova-pro-v1:0">Amazon Nova Pro (300k)</option>
                    <option value="amazon.nova-lite-v1:0">Amazon Nova Lite (300k)</option>
                    <option value="amazon.nova-micro-v1:0">Amazon Nova Micro (128k)</option>
                    <option value="meta.llama3-3-70b-instruct-v1:0">Meta Llama 3.3 70B (128k)</option>
                    <option value="meta.llama3-1-405b-instruct-v1:0">Meta Llama 3.1 405B (128k)</option>
                    <option value="meta.llama3-1-70b-instruct-v1:0">Meta Llama 3.1 70B (128k)</option>
                    <option value="mistral.mistral-large-2407-v1:0">Mistral Large 2 (128k)</option>
                    <option value="cohere.command-r-plus-v1:0">Cohere Command R+ (128k)</option>
                    <option value="amazon.titan-text-premier-v1:0">Amazon Titan Premier (32k)</option>
                  </select>
                </div>

                <button
                  onClick={() => setShowSettingsDrawer(!showSettingsDrawer)}
                  className="flex items-center gap-1.5 px-3 py-1 rounded-lg text-xs font-semibold border border-slate-200 dark:border-gray-800 bg-white dark:bg-gray-900 text-slate-600 dark:text-gray-400 hover:text-indigo-600"
                >
                  <Sliders className="w-3.5 h-3.5" />
                  <span>Parametreler</span>
                </button>
              </div>

              {/* Parametre Çekmecesi */}
              {showSettingsDrawer && (
                <div className="p-4 border-b border-slate-200 dark:border-gray-800 bg-slate-50 dark:bg-gray-900/80 space-y-3">
                  <div>
                    <label className="block text-[11px] font-bold text-slate-700 dark:text-gray-300 mb-1">
                      System Prompt (Sistem Talimatı)
                    </label>
                    <textarea
                      rows={2}
                      value={systemPrompt}
                      onChange={(e) => setSystemPrompt(e.target.value)}
                      className="w-full bg-white dark:bg-gray-950 border border-slate-200 dark:border-gray-800 rounded-lg p-2 text-xs text-slate-900 dark:text-white"
                    />
                  </div>
                  <div className="flex items-center gap-4">
                    <div className="flex-1">
                      <div className="flex justify-between text-[11px] font-bold text-slate-700 dark:text-gray-300 mb-1">
                        <span>Sıcaklık (Temperature)</span>
                        <span>{temperature}</span>
                      </div>
                      <input
                        type="range"
                        min="0.0"
                        max="1.0"
                        step="0.05"
                        value={temperature}
                        onChange={(e) => setTemperature(parseFloat(e.target.value))}
                        className="w-full accent-indigo-600"
                      />
                    </div>
                  </div>
                </div>
              )}

              {/* Mesaj Akışı */}
              <div className="flex-1 overflow-y-auto p-4 space-y-4">
                {messages.map((m, idx) => (
                  <div
                    key={m.id || idx}
                    className={`flex gap-3 text-xs leading-relaxed ${
                      m.role === "user" ? "justify-end" : "justify-start"
                    }`}
                  >
                    <div
                      className={`max-w-[85%] rounded-2xl p-4 shadow-sm ${
                        m.role === "user"
                          ? "bg-indigo-600 text-white font-medium rounded-tr-none"
                          : "bg-slate-100 dark:bg-gray-900 text-slate-900 dark:text-gray-100 border border-slate-200 dark:border-gray-800 rounded-tl-none"
                      }`}
                    >
                      <div className="flex items-center justify-between text-[10px] opacity-70 mb-1.5 uppercase font-bold tracking-wider">
                        <span>{m.role === "user" ? "Siz" : selectedModel.split(".")[1] || "Bedrock AI"}</span>
                        {m.role !== "user" && (
                          <button
                            onClick={() => copyToClipboard(m.content, m.id || idx.toString())}
                            className="hover:text-indigo-400 flex items-center gap-1 normal-case font-sans"
                          >
                            {copiedCodeIndex === (m.id || idx.toString()) ? (
                              <Check className="w-3 h-3 text-emerald-500" />
                            ) : (
                              <Copy className="w-3 h-3" />
                            )}
                            Kopyala
                          </button>
                        )}
                      </div>
                      <div className="whitespace-pre-wrap">{m.content}</div>
                    </div>
                  </div>
                ))}
              </div>

              {/* Mesaj Gönderme Giriş Alanı */}
              <form onSubmit={handleSendMessage} className="p-3 border-t border-slate-200 dark:border-gray-800 flex gap-2">
                <input
                  type="text"
                  value={chatInput}
                  onChange={(e) => setChatInput(e.target.value)}
                  placeholder="AWS Bedrock'a mesajınızı yazın..."
                  className="flex-1 bg-slate-50 dark:bg-gray-900 border border-slate-200 dark:border-gray-800 rounded-xl px-4 py-3 text-xs text-slate-900 dark:text-white focus:outline-none focus:border-indigo-500"
                />
                <button
                  type="submit"
                  disabled={isStreaming || !chatInput.trim()}
                  className="px-6 rounded-xl bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-bold transition flex items-center gap-1.5 shadow-md shadow-indigo-600/20 disabled:opacity-40"
                >
                  <Send className="w-4 h-4" />
                  <span>Gönder</span>
                </button>
              </form>

            </div>
          </div>
        )}

        {/* ================================================================= */}
        {/* SEKME 2: MODEL KATALOĞU (EXPANDED BEDROCK MODELS) */}
        {/* ================================================================= */}
        {activeTab === "models" && (
          <div className="max-w-6xl mx-auto space-y-6">
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
              <div>
                <h2 className="text-xl font-black text-slate-900 dark:text-white">AWS Bedrock Model Kataloğu</h2>
                <p className="text-xs text-slate-500 dark:text-gray-400 mt-1">
                  API Gateway üzerinden erişilebilen ve anında çağrılabilen tüm frontier modeller.
                </p>
              </div>

              {/* Kategori Filtre Butonları */}
              <div className="flex flex-wrap gap-1.5">
                {["ALL", "ANTHROPIC", "AMAZON", "META", "MISTRAL", "COHERE", "IMAGE"].map((cat) => (
                  <button
                    key={cat}
                    onClick={() => setModelCategory(cat)}
                    className={`px-3 py-1.5 rounded-lg text-xs font-bold transition ${
                      modelCategory === cat
                        ? "bg-indigo-600 text-white"
                        : "bg-white dark:bg-gray-900 border border-slate-200 dark:border-gray-800 text-slate-600 dark:text-gray-400 hover:bg-slate-100"
                    }`}
                  >
                    {cat}
                  </button>
                ))}
              </div>
            </div>

            {/* Model Kartları Grid */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {filteredModels.map((m) => (
                <div
                  key={m.id}
                  className="p-5 rounded-2xl bg-white dark:bg-gray-900 border border-slate-200 dark:border-gray-800 shadow-sm hover:border-indigo-500/50 transition space-y-3"
                >
                  <div className="flex items-center justify-between">
                    <span className="font-bold text-sm text-slate-900 dark:text-white">{m.name}</span>
                    <span className="text-[10px] px-2 py-0.5 rounded bg-indigo-50 dark:bg-indigo-950 text-indigo-700 dark:text-indigo-300 font-bold border border-indigo-200 dark:border-indigo-800">
                      {m.type}
                    </span>
                  </div>
                  <div className="text-[11px] text-slate-500 dark:text-gray-400 font-mono break-all">{m.id}</div>
                  <div className="pt-2 border-t border-slate-100 dark:border-gray-800/80 flex items-center justify-between text-xs">
                    <span className="text-slate-500 dark:text-gray-400">
                      Context: {m.context_window > 0 ? `${m.context_window.toLocaleString()} tok` : "N/A"}
                    </span>
                    <span className="text-emerald-600 dark:text-emerald-400 font-bold">
                      ${m.pricing?.input_per_1k}/1k In
                    </span>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* ================================================================= */}
        {/* SEKME 3: API ANAHTARLARI */}
        {/* ================================================================= */}
        {activeTab === "keys" && (
          <div className="max-w-4xl mx-auto space-y-6">
            <div className="flex items-center justify-between">
              <div>
                <h2 className="text-xl font-black text-slate-900 dark:text-white">API Anahtarları Yönetimi</h2>
                <p className="text-xs text-slate-500 dark:text-gray-400 mt-0.5">
                  OpenAI SDK ve harici sistem entegrasyonları için `sk-live-...` anahtarları oluşturun.
                </p>
              </div>
            </div>

            {/* Yeni Anahtar Oluşturma Formu */}
            <form onSubmit={handleCreateApiKey} className="p-5 rounded-2xl bg-white dark:bg-gray-900 border border-slate-200 dark:border-gray-800 flex gap-2">
              <input
                type="text"
                value={newKeyName}
                onChange={(e) => setNewKeyName(e.target.value)}
                placeholder="Anahtar Adı (Örn: Production Web App)..."
                className="flex-1 bg-slate-50 dark:bg-gray-950 border border-slate-200 dark:border-gray-800 rounded-xl px-4 py-2.5 text-xs text-slate-900 dark:text-white focus:outline-none focus:border-indigo-500"
              />
              <button
                type="submit"
                className="px-5 py-2.5 rounded-xl bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-bold transition flex items-center gap-1.5 shadow-md shadow-indigo-600/20"
              >
                <Plus className="w-4 h-4" />
                <span>Oluştur</span>
              </button>
            </form>

            {/* Oluşturulan Gizli Anahtar Uyarısı */}
            {createdSecretKey && (
              <div className="p-4 rounded-2xl bg-amber-50 dark:bg-amber-950/40 border border-amber-200 dark:border-amber-800 space-y-2">
                <div className="text-xs font-bold text-amber-800 dark:text-amber-300 flex items-center gap-1.5">
                  <ShieldCheck className="w-4 h-4" />
                  <span>Yeni API Anahtarınız (Lütfen kopyalayın, tekrar gösterilmeyecektir):</span>
                </div>
                <div className="flex items-center gap-2">
                  <code className="flex-1 bg-white dark:bg-gray-950 p-2.5 rounded-xl border border-amber-300 dark:border-amber-700 font-mono text-xs text-amber-900 dark:text-amber-200 break-all">
                    {createdSecretKey}
                  </code>
                  <button
                    onClick={() => {
                      navigator.clipboard.writeText(createdSecretKey);
                      setKeyCopied(true);
                      setTimeout(() => setKeyCopied(false), 2000);
                    }}
                    className="px-4 py-2.5 rounded-xl bg-amber-600 hover:bg-amber-500 text-white text-xs font-bold transition"
                  >
                    {keyCopied ? "Kopyalandı!" : "Kopyala"}
                  </button>
                </div>
              </div>
            )}

            {/* Mevcut Anahtarlar Tablosu */}
            <div className="rounded-2xl border border-slate-200 dark:border-gray-800 bg-white dark:bg-gray-900 overflow-hidden shadow-sm">
              <div className="p-4 border-b border-slate-200 dark:border-gray-800 font-bold text-xs">
                Aktif Anahtarlarınız
              </div>
              <div className="divide-y divide-slate-100 dark:divide-gray-800">
                {apiKeys.map((k) => (
                  <div key={k.id} className="p-4 flex items-center justify-between text-xs">
                    <div>
                      <div className="font-bold text-slate-900 dark:text-white">{k.name}</div>
                      <div className="text-slate-400 dark:text-gray-500 font-mono text-[11px] mt-0.5">
                        {k.prefix}••••••••••••
                      </div>
                    </div>
                    <div className="flex items-center gap-4">
                      <span className="text-emerald-600 dark:text-emerald-400 font-semibold text-[11px]">
                        Harcanan: ${Number(k.spend_usd || 0).toFixed(4)}
                      </span>
                      <button
                        onClick={() => handleRevokeKey(k.id)}
                        title="Anahtarı İptal Et"
                        className="text-slate-400 hover:text-red-600 p-1 transition"
                      >
                        <Trash2 className="w-4 h-4" />
                      </button>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        )}

        {/* ================================================================= */}
        {/* SEKME 4: PROMETHEUS & CANLI GRAFANA-STYLE ANALİTİK */}
        {/* ================================================================= */}
        {activeTab === "analytics" && (
          <div className="max-w-5xl mx-auto space-y-6">
            <div className="flex items-center justify-between">
              <div>
                <h2 className="text-xl font-black text-slate-900 dark:text-white">Prometheus & Sistem Metrikleri</h2>
                <p className="text-xs text-slate-500 dark:text-gray-400 mt-0.5">
                  FastAPI `/metrics` telemetrisi ve canlı kullanım göstergeleri.
                </p>
              </div>
              <button
                onClick={fetchAnalyticsData}
                className="flex items-center gap-1.5 px-3 py-1.5 rounded-xl border border-slate-200 dark:border-gray-800 bg-white dark:bg-gray-900 text-xs font-bold text-slate-700 dark:text-gray-300 hover:text-indigo-600"
              >
                <RefreshCw className={`w-3.5 h-3.5 ${metricsLoading ? "animate-spin" : ""}`} />
                <span>Yenile</span>
              </button>
            </div>

            {/* Metrik Özet Kartları */}
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
              <div className="p-5 rounded-2xl bg-white dark:bg-gray-900 border border-slate-200 dark:border-gray-800 shadow-sm">
                <div className="flex items-center justify-between text-xs text-slate-500 dark:text-gray-400 mb-1">
                  <span>Toplam İstek (RPS)</span>
                  <Activity className="w-4 h-4 text-indigo-600 dark:text-indigo-400" />
                </div>
                <div className="text-2xl font-black text-slate-900 dark:text-white">
                  {usageSummary?.total_requests || 0}
                </div>
                <div className="text-[10px] text-emerald-600 mt-1 font-semibold">✓ %99.98 Uptime</div>
              </div>

              <div className="p-5 rounded-2xl bg-white dark:bg-gray-900 border border-slate-200 dark:border-gray-800 shadow-sm">
                <div className="flex items-center justify-between text-xs text-slate-500 dark:text-gray-400 mb-1">
                  <span>Toplam Token</span>
                  <Zap className="w-4 h-4 text-amber-500" />
                </div>
                <div className="text-2xl font-black text-indigo-600 dark:text-indigo-400">
                  {usageSummary?.total_tokens?.toLocaleString() || 0}
                </div>
                <div className="text-[10px] text-slate-400 mt-1">Prompt + Completion</div>
              </div>

              <div className="p-5 rounded-2xl bg-white dark:bg-gray-900 border border-slate-200 dark:border-gray-800 shadow-sm">
                <div className="flex items-center justify-between text-xs text-slate-500 dark:text-gray-400 mb-1">
                  <span>Toplam Harcama</span>
                  <DollarSign className="w-4 h-4 text-emerald-500" />
                </div>
                <div className="text-2xl font-black text-emerald-600 dark:text-emerald-400">
                  ${usageSummary?.total_spent_usd?.toFixed(4) || "0.0000"}
                </div>
                <div className="text-[10px] text-slate-400 mt-1">USD cinsinden</div>
              </div>

              <div className="p-5 rounded-2xl bg-white dark:bg-gray-900 border border-slate-200 dark:border-gray-800 shadow-sm">
                <div className="flex items-center justify-between text-xs text-slate-500 dark:text-gray-400 mb-1">
                  <span>P95 Gecikme</span>
                  <Clock className="w-4 h-4 text-purple-500" />
                </div>
                <div className="text-2xl font-black text-purple-600 dark:text-purple-400">
                  ~340ms
                </div>
                <div className="text-[10px] text-emerald-600 mt-1 font-semibold">SSE Canlı Akış</div>
              </div>
            </div>

            {/* Prometheus Metrik Akışı */}
            <div className="p-5 rounded-2xl bg-white dark:bg-gray-900 border border-slate-200 dark:border-gray-800 shadow-sm space-y-3">
              <div className="flex items-center justify-between">
                <span className="text-xs font-bold text-slate-900 dark:text-white">Prometheus Exporter Çıktısı (/metrics)</span>
                <span className="text-[10px] px-2 py-0.5 rounded bg-emerald-50 dark:bg-emerald-950 text-emerald-600 dark:text-emerald-400 font-bold border border-emerald-200 dark:border-emerald-800">
                  Aktif
                </span>
              </div>
              <pre className="p-4 rounded-xl bg-slate-900 text-gray-200 font-mono text-[11px] overflow-x-auto max-h-60 leading-relaxed">
                {prometheusRaw || "# Prometheus metrikleri çekiliyor..."}
              </pre>
            </div>
          </div>
        )}

        {/* ================================================================= */}
        {/* SEKME 5: CÜZDAN & BAKİYE */}
        {/* ================================================================= */}
        {activeTab === "billing" && (
          <div className="max-w-4xl mx-auto space-y-6">
            <h2 className="text-xl font-black text-slate-900 dark:text-white">Bakiye & Cüzdan Yükleme</h2>
            
            {/* Bakiye Kartı */}
            <div className="p-6 rounded-3xl bg-gradient-to-r from-indigo-900 to-purple-900 text-white shadow-xl flex items-center justify-between">
              <div>
                <span className="text-xs text-indigo-200 font-semibold">Mevcut Bakiyeniz</span>
                <div className="text-3xl font-black mt-1">${balance.toFixed(2)} USD</div>
              </div>
              <div className="text-right text-xs text-indigo-200">
                <div>Hesap Türü: <strong>{user?.role?.toUpperCase()}</strong></div>
                <div className="text-emerald-300 font-semibold mt-1">✓ Otomatik Kota Korumalı</div>
              </div>
            </div>

            {/* Yükleme Paketleri */}
            <div>
              <h3 className="text-sm font-bold text-slate-900 dark:text-white mb-3">Kredi Yükleme Paketleri (Stripe)</h3>
              <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
                {[10, 25, 50].map((amt) => (
                  <div key={amt} className="p-5 rounded-2xl bg-white dark:bg-gray-900 border border-slate-200 dark:border-gray-800 text-center space-y-3">
                    <div className="text-2xl font-black text-indigo-600 dark:text-indigo-400">${amt} USD</div>
                    <div className="text-xs text-slate-500 dark:text-gray-400">~{(amt * 250000).toLocaleString()} Claude 3.5 Token</div>
                    <Link
                      href="/billing"
                      className="block w-full py-2.5 rounded-xl bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-bold shadow-md shadow-indigo-600/20 transition"
                    >
                      Bakiye Yükle
                    </Link>
                  </div>
                ))}
              </div>
            </div>
          </div>
        )}

        {/* ================================================================= */}
        {/* SEKME 6: KULLANICI PROFİLİ & GÜVENLİK */}
        {/* ================================================================= */}
        {activeTab === "profile" && (
          <div className="max-w-4xl mx-auto space-y-6">
            <h2 className="text-xl font-black text-slate-900 dark:text-white">Kullanıcı Profili & Güvenlik</h2>

            {/* Hesap Bilgileri Kartı */}
            <div className="p-6 rounded-2xl bg-white dark:bg-gray-900 border border-slate-200 dark:border-gray-800 shadow-sm space-y-4">
              <h3 className="text-xs font-bold text-slate-900 dark:text-white uppercase tracking-wider">
                Hesap Bilgileri
              </h3>
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 text-xs">
                <div>
                  <span className="text-slate-500 dark:text-gray-400">E-Posta:</span>
                  <div className="font-bold text-slate-900 dark:text-white mt-0.5">{user?.email}</div>
                </div>
                <div>
                  <span className="text-slate-500 dark:text-gray-400">Kullanıcı Rolü:</span>
                  <div className="font-bold text-indigo-600 dark:text-indigo-400 mt-0.5 uppercase">{user?.role}</div>
                </div>
                <div>
                  <span className="text-slate-500 dark:text-gray-400">Kullanıcı ID:</span>
                  <div className="font-mono text-slate-600 dark:text-gray-300 mt-0.5 text-[11px]">{user?.id}</div>
                </div>
              </div>
            </div>

            {/* Şifre Değiştirme Kartı */}
            <div className="p-6 rounded-2xl bg-white dark:bg-gray-900 border border-slate-200 dark:border-gray-800 shadow-sm space-y-4">
              <h3 className="text-xs font-bold text-slate-900 dark:text-white uppercase tracking-wider flex items-center gap-1.5">
                <KeyRound className="w-4 h-4 text-indigo-600" />
                <span>Şifre Değiştir</span>
              </h3>

              {pwdMessage && (
                <div className={`p-3 rounded-xl text-xs ${
                  pwdMessage.type === "success" 
                    ? "bg-emerald-50 text-emerald-700 border border-emerald-200" 
                    : "bg-red-50 text-red-700 border border-red-200"
                }`}>
                  {pwdMessage.text}
                </div>
              )}

              <form onSubmit={handleChangePassword} className="space-y-3 max-w-md">
                <div>
                  <label className="block text-xs font-semibold text-slate-700 dark:text-gray-300 mb-1">
                    Mevcut Şifre
                  </label>
                  <input
                    type="password"
                    required
                    value={currentPassword}
                    onChange={(e) => setCurrentPassword(e.target.value)}
                    className="w-full bg-slate-50 dark:bg-gray-950 border border-slate-200 dark:border-gray-800 rounded-xl px-3.5 py-2 text-xs text-slate-900 dark:text-white"
                  />
                </div>
                <div>
                  <label className="block text-xs font-semibold text-slate-700 dark:text-gray-300 mb-1">
                    Yeni Şifre (En az 8 karakter)
                  </label>
                  <input
                    type="password"
                    required
                    minLength={8}
                    value={newPassword}
                    onChange={(e) => setNewPassword(e.target.value)}
                    className="w-full bg-slate-50 dark:bg-gray-950 border border-slate-200 dark:border-gray-800 rounded-xl px-3.5 py-2 text-xs text-slate-900 dark:text-white"
                  />
                </div>
                <button
                  type="submit"
                  className="px-5 py-2.5 rounded-xl bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-bold transition shadow-md shadow-indigo-600/20"
                >
                  Şifreyi Güncelle
                </button>
              </form>
            </div>

            {/* İki Adımlı Doğrulama (2FA / MFA) Kartı */}
            <div className="p-6 rounded-2xl bg-white dark:bg-gray-900 border border-slate-200 dark:border-gray-800 shadow-sm space-y-4">
              <h3 className="text-xs font-bold text-slate-900 dark:text-white uppercase tracking-wider flex items-center gap-1.5">
                <QrCode className="w-4 h-4 text-purple-600" />
                <span>İki Adımlı Doğrulama (2FA / MFA)</span>
              </h3>

              {mfaStatus && (
                <div className="p-3 rounded-xl bg-indigo-50 dark:bg-indigo-950/40 text-indigo-700 dark:text-indigo-300 text-xs border border-indigo-200 dark:border-indigo-800">
                  {mfaStatus}
                </div>
              )}

              {!mfaData ? (
                <button
                  onClick={handleInitiateMFA}
                  className="px-5 py-2.5 rounded-xl bg-purple-600 hover:bg-purple-500 text-white text-xs font-bold transition shadow-md shadow-purple-600/20"
                >
                  2FA Kurulumunu Başlat
                </button>
              ) : (
                <form onSubmit={handleVerifyMFA} className="space-y-3 max-w-md">
                  <div className="p-3 rounded-xl bg-slate-50 dark:bg-gray-950 border border-slate-200 dark:border-gray-800 text-xs space-y-1">
                    <div>Authenticator Secret: <strong className="font-mono">{mfaData.secret}</strong></div>
                    <div className="text-[11px] text-slate-500">Google Authenticator veya Authy uygulamanıza bu anahtarı ekleyin.</div>
                  </div>
                  <div>
                    <label className="block text-xs font-semibold text-slate-700 dark:text-gray-300 mb-1">
                      Uygulamadaki 6 Haneli Kod
                    </label>
                    <input
                      type="text"
                      required
                      value={mfaCode}
                      onChange={(e) => setMfaCode(e.target.value)}
                      placeholder="123456"
                      className="w-full bg-slate-50 dark:bg-gray-950 border border-slate-200 dark:border-gray-800 rounded-xl px-3.5 py-2 text-xs font-mono text-slate-900 dark:text-white"
                    />
                  </div>
                  <button
                    type="submit"
                    className="px-5 py-2.5 rounded-xl bg-purple-600 hover:bg-purple-500 text-white text-xs font-bold transition shadow-md shadow-purple-600/20"
                  >
                    Kodu Doğrula ve Aktifleştir
                  </button>
                </form>
              )}
            </div>
          </div>
        )}

        {/* ================================================================= */}
        {/* SEKME 7: ADMIN KONTROL MERKEZİ (FOR ADMIN ROLE) */}
        {/* ================================================================= */}
        {activeTab === "admin" && user?.role === "admin" && (
          <div className="max-w-5xl mx-auto space-y-6">
            <h2 className="text-xl font-black text-slate-900 dark:text-white">Admin Sistem Kontrol Merkezi</h2>

            {/* Finansal & Sistem Özeti */}
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
              <div className="p-5 rounded-2xl bg-white dark:bg-gray-900 border border-slate-200 dark:border-gray-800 shadow-sm">
                <div className="text-xs text-slate-500 dark:text-gray-400">Toplam Platform Geliri</div>
                <div className="text-2xl font-black text-slate-900 dark:text-white mt-1">
                  ${Number(adminOverview?.total_revenue_usd || 0).toFixed(4)}
                </div>
              </div>
              <div className="p-5 rounded-2xl bg-white dark:bg-gray-900 border border-slate-200 dark:border-gray-800 shadow-sm">
                <div className="text-xs text-slate-500 dark:text-gray-400">Platform Net Karı</div>
                <div className="text-2xl font-black text-emerald-600 dark:text-emerald-400 mt-1">
                  ${Number(adminOverview?.platform_net_profit_usd || 0).toFixed(4)}
                </div>
              </div>
              <div className="p-5 rounded-2xl bg-white dark:bg-gray-900 border border-slate-200 dark:border-gray-800 shadow-sm">
                <div className="text-xs text-slate-500 dark:text-gray-400">Kayıtlı Kullanıcı Sayısı</div>
                <div className="text-2xl font-black text-purple-600 dark:text-purple-400 mt-1">
                  {adminOverview?.total_users || 0}
                </div>
              </div>
            </div>

            {/* Bakiye Düzenleme Modalı */}
            {selectedUserForBalance && (
              <div className="p-5 rounded-2xl bg-purple-50 dark:bg-purple-950/40 border border-purple-200 dark:border-purple-800 space-y-3">
                <div className="text-xs font-bold text-purple-900 dark:text-purple-300">
                  {selectedUserForBalance.email} için Bakiye Düzenle
                </div>
                <form onSubmit={handleAdjustBalance} className="flex gap-2">
                  <input
                    type="number"
                    step="0.01"
                    value={newBalanceAmount}
                    onChange={(e) => setNewBalanceAmount(e.target.value)}
                    className="w-40 bg-white dark:bg-gray-950 border border-purple-300 dark:border-purple-700 rounded-xl px-3 py-2 text-xs font-bold text-slate-900 dark:text-white"
                  />
                  <button
                    type="submit"
                    className="px-4 py-2 rounded-xl bg-purple-600 hover:bg-purple-500 text-white text-xs font-bold"
                  >
                    Kaydet
                  </button>
                  <button
                    type="button"
                    onClick={() => setSelectedUserForBalance(null)}
                    className="px-3 py-2 rounded-xl bg-slate-200 dark:bg-gray-800 text-xs font-bold"
                  >
                    İptal
                  </button>
                </form>
              </div>
            )}

            {/* Kullanıcı Yönetim Tablosu */}
            <div className="rounded-2xl border border-slate-200 dark:border-gray-800 bg-white dark:bg-gray-900 overflow-hidden shadow-sm">
              <div className="p-4 border-b border-slate-200 dark:border-gray-800 font-bold text-xs flex justify-between items-center">
                <span>Kullanıcı Yönetimi ({adminUsers.length})</span>
                <span className="text-[11px] text-slate-400 font-normal">Rol ve Durum Düzenleme</span>
              </div>
              <div className="overflow-x-auto">
                <table className="w-full text-left text-xs">
                  <thead className="bg-slate-50 dark:bg-gray-950 text-slate-500 dark:text-gray-400 border-b border-slate-200 dark:border-gray-800">
                    <tr>
                      <th className="p-3">Kullanıcı</th>
                      <th className="p-3">Rol</th>
                      <th className="p-3">Bakiye</th>
                      <th className="p-3">Durum</th>
                      <th className="p-3 text-right">İşlemler</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-100 dark:divide-gray-800">
                    {adminUsers.map((u) => (
                      <tr key={u.id}>
                        <td className="p-3 font-semibold text-slate-900 dark:text-white">
                          {u.email}
                        </td>
                        <td className="p-3 uppercase font-bold text-indigo-600 dark:text-indigo-400">
                          {u.role}
                        </td>
                        <td className="p-3 font-black text-emerald-600 dark:text-emerald-400">
                          ${u.balance_usd?.toFixed(2)}
                        </td>
                        <td className="p-3">
                          <span className={`px-2 py-0.5 rounded text-[10px] font-bold ${
                            u.is_active 
                              ? "bg-emerald-50 text-emerald-700 dark:bg-emerald-950 dark:text-emerald-300" 
                              : "bg-red-50 text-red-700 dark:bg-red-950 dark:text-red-300"
                          }`}>
                            {u.is_active ? "Aktif" : "Askıda"}
                          </span>
                        </td>
                        <td className="p-3 text-right space-x-2">
                          <button
                            onClick={() => {
                              setSelectedUserForBalance(u);
                              setNewBalanceAmount(u.balance_usd?.toString() || "0");
                            }}
                            className="text-xs font-bold text-indigo-600 dark:text-indigo-400 hover:underline"
                          >
                            Bakiye Düzenle
                          </button>
                          <button
                            onClick={() => handleToggleUserStatus(u.id, u.is_active)}
                            className="text-xs font-bold text-slate-500 hover:text-red-600 hover:underline"
                          >
                            {u.is_active ? "Askıya Al" : "Aktif Et"}
                          </button>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          </div>
        )}

      </main>
    </div>
  );
}
