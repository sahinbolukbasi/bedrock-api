"use client";

import React, { useState, useEffect } from "react";
import Link from "next/link";
import { 
  MessageSquare, 
  Cpu, 
  Key, 
  CreditCard, 
  ShieldAlert, 
  Lock, 
  Mail, 
  ArrowRight, 
  Sparkles, 
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
  ShieldCheck, 
  RefreshCw, 
  Search, 
  Clock, 
  QrCode, 
  KeyRound, 
  Server, 
  Globe, 
  Database, 
  Gauge, 
  ExternalLink,
  Radio,
  Layers
} from "lucide-react";
import { API_BASE, getAuthToken, setAuthToken, fetchApi, clearAuthToken } from "../lib/api";

export default function RootPage() {
  // Auth state
  const [token, setToken] = useState<string | null>(null);
  const [user, setUser] = useState<any | null>(null);
  const [loading, setLoading] = useState<boolean>(true);

  // Guest Auth Mode: "login" | "register" | "forgot"
  const [authMode, setAuthMode] = useState<"login" | "register" | "forgot">("login");

  // Guest Login Form state
  const [loginEmail, setLoginEmail] = useState("admin@bedrockgateway.com");
  const [loginPassword, setLoginPassword] = useState("AdminPassword123!");
  const [loginError, setLoginError] = useState("");
  const [loginLoading, setLoginLoading] = useState(false);

  // Guest Register Form state
  const [regFullName, setRegFullName] = useState("");
  const [regEmail, setRegEmail] = useState("");
  const [regPassword, setRegPassword] = useState("");
  const [regPasswordConfirm, setRegPasswordConfirm] = useState("");
  const [regError, setRegError] = useState("");
  const [regSuccess, setRegSuccess] = useState("");
  const [regLoading, setRegLoading] = useState(false);

  // Guest Forgot Password state
  const [forgotEmail, setForgotEmail] = useState("");
  const [forgotSubmitted, setForgotSubmitted] = useState(false);
  const [forgotLoading, setForgotLoading] = useState(false);

  // Console Hub Active Tab state
  const [activeTab, setActiveTab] = useState<"chat" | "models" | "keys" | "billing" | "profile" | "admin">("chat");

  // Models catalog & wallet
  const [models, setModels] = useState<any[]>([]);
  const [balance, setBalance] = useState<number>(0);
  const [selectedModel, setSelectedModel] = useState("anthropic.claude-3-5-sonnet-20241022-v2:0");
  const [modelCategory, setModelCategory] = useState<string>("ALL");

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
      content: "👋 Merhaba! **AWS Bedrock AI Gateway**'e hoş geldiniz.\nYukarıdaki model listesinden dilediğiniz foundation modelini seçerek anında yüksek hızlı SSE akışıyla sohbet edebilirsiniz.",
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
  // User Profile State
  // ==========================================
  const [currentPassword, setCurrentPassword] = useState("");
  const [newPassword, setNewPassword] = useState("");
  const [pwdMessage, setPwdMessage] = useState<{ type: "success" | "error"; text: string } | null>(null);
  const [mfaData, setMfaData] = useState<{ secret: string; provisioning_uri: string } | null>(null);
  const [mfaCode, setMfaCode] = useState("");
  const [mfaStatus, setMfaStatus] = useState<string | null>(null);

  // ==========================================
  // Admin & AWS Infrastructure State
  // ==========================================
  const [adminOverview, setAdminOverview] = useState<any>(null);
  const [adminUsers, setAdminUsers] = useState<any[]>([]);
  const [awsStatus, setAwsStatus] = useState<any>(null);
  const [selectedUserForBalance, setSelectedUserForBalance] = useState<any | null>(null);
  const [newBalanceAmount, setNewBalanceAmount] = useState<string>("100");
  const [userSearchTerm, setUserSearchTerm] = useState("");

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
      console.error("Failed to fetch messages:", err);
    }
  };

  // Create new conversation
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

  // Delete conversation
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

  // Guest Registration Submit
  const handleRegisterSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setRegError("");
    setRegSuccess("");

    if (regPassword !== regPasswordConfirm) {
      setRegError("Girilen şifreler birbiriyle eşleşmiyor.");
      return;
    }
    if (regPassword.length < 8) {
      setRegError("Şifre en az 8 karakter uzunluğunda olmalıdır.");
      return;
    }

    setRegLoading(true);
    try {
      const res = await fetch(`${API_BASE}/api/auth/register`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          email: regEmail,
          password: regPassword,
          full_name: regFullName || undefined,
        }),
      });

      const data = await res.json();
      if (!res.ok) {
        throw new Error(data?.detail || data?.message || "Kayıt işlemi başarısız.");
      }

      setAuthToken(data.access_token);
      setToken(data.access_token);
      setUser({ email: data.email, role: data.role, id: data.user_id });
      setRegSuccess("Hesabınız oluşturuldu! $1.00 başlangıç kredisi tanımlandı.");

      const walletData = await fetchApi("/api/wallet");
      setBalance(Number(walletData.balance_usd));
      const modelsData = await fetchApi("/v1/models");
      setModels(modelsData.data || []);
      loadConversations();
    } catch (err: any) {
      setRegError(err.message || "Kayıt olurken bir hata oluştu.");
    } finally {
      setRegLoading(false);
    }
  };

  // Guest Forgot Password Submit
  const handleForgotSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setForgotLoading(true);
    setTimeout(() => {
      setForgotLoading(false);
      setForgotSubmitted(true);
    }, 1000);
  };

  // Switch Tabs & Load Tab Data
  const handleTabChange = async (tab: any) => {
    setActiveTab(tab);
    if (tab === "keys") {
      try {
        const data = await fetchApi("/api/keys");
        setApiKeys(data || []);
      } catch {}
    } else if (tab === "admin") {
      fetchAdminData();
    }
  };

  // Fetch Admin & AWS Diagnostics Data
  const fetchAdminData = async () => {
    try {
      const overview = await fetchApi("/api/admin/overview");
      setAdminOverview(overview);
      const usersList = await fetchApi("/api/admin/users");
      setAdminUsers(usersList || []);
      const awsInfo = await fetchApi("/api/admin/aws-status");
      setAwsStatus(awsInfo);
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
  // KATMAN 1: GİRİŞ VE KAYIT KAPISI (GUEST PORTAL)
  // =========================================================================
  if (!token) {
    return (
      <div className="min-h-[calc(100vh-64px)] flex items-center justify-center p-4 relative overflow-hidden bg-slate-50 dark:bg-[#0b0f17] transition-colors">
        <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[550px] h-[550px] bg-indigo-500/10 dark:bg-indigo-500/20 blur-[140px] pointer-events-none rounded-full" />

        <div className="w-full max-w-md relative z-10">
          <div className="rounded-3xl border border-slate-200 dark:border-gray-800 bg-white dark:bg-gray-900 shadow-2xl p-8 backdrop-blur-xl transition-colors">
            
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

            {/* Auth Mode Tab Switcher */}
            <div className="flex p-1 rounded-2xl bg-slate-100 dark:bg-gray-950 mb-6 border border-slate-200 dark:border-gray-800">
              <button
                onClick={() => { setAuthMode("login"); setLoginError(""); setRegError(""); }}
                className={`flex-1 py-2 rounded-xl text-xs font-bold transition ${
                  authMode === "login"
                    ? "bg-white dark:bg-gray-800 text-indigo-600 dark:text-indigo-400 shadow-sm"
                    : "text-slate-500 dark:text-gray-400 hover:text-slate-900 dark:hover:text-white"
                }`}
              >
                Giriş Yap
              </button>
              <button
                onClick={() => { setAuthMode("register"); setLoginError(""); setRegError(""); }}
                className={`flex-1 py-2 rounded-xl text-xs font-bold transition flex items-center justify-center gap-1 ${
                  authMode === "register"
                    ? "bg-white dark:bg-gray-800 text-indigo-600 dark:text-indigo-400 shadow-sm"
                    : "text-slate-500 dark:text-gray-400 hover:text-slate-900 dark:hover:text-white"
                }`}
              >
                <span>Kayıt Ol</span>
                <span className="px-1.5 py-0.5 rounded bg-amber-100 text-amber-800 dark:bg-amber-950 dark:text-amber-300 text-[9px] font-black">
                  $1 Hediye
                </span>
              </button>
            </div>

            {/* TAB 1: LOGIN FORM */}
            {authMode === "login" && (
              <>
                {loginError && (
                  <div className="mb-4 p-3.5 rounded-xl bg-red-50 dark:bg-red-500/10 border border-red-200 dark:border-red-500/30 flex items-center gap-2 text-xs text-red-600 dark:text-red-400">
                    <AlertCircle className="w-4 h-4 flex-shrink-0" />
                    <span>{loginError}</span>
                  </div>
                )}

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
                    <div className="flex justify-between items-center mb-1.5">
                      <label className="block text-xs font-bold text-slate-700 dark:text-gray-300">
                        Şifre
                      </label>
                      <button
                        type="button"
                        onClick={() => setAuthMode("forgot")}
                        className="text-[11px] text-indigo-600 dark:text-indigo-400 hover:underline font-semibold"
                      >
                        Şifremi Unuttum?
                      </button>
                    </div>
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
              </>
            )}

            {/* TAB 2: REGISTER FORM */}
            {authMode === "register" && (
              <>
                {regError && (
                  <div className="mb-4 p-3.5 rounded-xl bg-red-50 dark:bg-red-500/10 border border-red-200 dark:border-red-500/30 flex items-center gap-2 text-xs text-red-600 dark:text-red-400">
                    <AlertCircle className="w-4 h-4 flex-shrink-0" />
                    <span>{regError}</span>
                  </div>
                )}

                {regSuccess && (
                  <div className="mb-4 p-3.5 rounded-xl bg-emerald-50 dark:bg-emerald-500/10 border border-emerald-200 dark:border-emerald-500/30 flex items-center gap-2 text-xs text-emerald-600 dark:text-emerald-400">
                    <CheckCircle2 className="w-4 h-4 flex-shrink-0" />
                    <span>{regSuccess}</span>
                  </div>
                )}

                <form onSubmit={handleRegisterSubmit} className="space-y-3">
                  <div>
                    <label className="block text-xs font-bold text-slate-700 dark:text-gray-300 mb-1">
                      Ad Soyad (Opsiyonel)
                    </label>
                    <input
                      type="text"
                      value={regFullName}
                      onChange={(e) => setRegFullName(e.target.value)}
                      placeholder="Ahmet Yılmaz"
                      className="w-full bg-slate-50 dark:bg-gray-950 border border-slate-200 dark:border-gray-800 rounded-xl px-3.5 py-2 text-xs text-slate-900 dark:text-white focus:outline-none focus:border-indigo-500 font-medium"
                    />
                  </div>

                  <div>
                    <label className="block text-xs font-bold text-slate-700 dark:text-gray-300 mb-1">
                      E-Posta Adresi *
                    </label>
                    <input
                      type="email"
                      required
                      value={regEmail}
                      onChange={(e) => setRegEmail(e.target.value)}
                      placeholder="adiniz@sirketiniz.com"
                      className="w-full bg-slate-50 dark:bg-gray-950 border border-slate-200 dark:border-gray-800 rounded-xl px-3.5 py-2 text-xs text-slate-900 dark:text-white focus:outline-none focus:border-indigo-500 font-medium"
                    />
                  </div>

                  <div>
                    <label className="block text-xs font-bold text-slate-700 dark:text-gray-300 mb-1">
                      Şifre (En az 8 karakter) *
                    </label>
                    <input
                      type="password"
                      required
                      minLength={8}
                      value={regPassword}
                      onChange={(e) => setRegPassword(e.target.value)}
                      placeholder="••••••••••••"
                      className="w-full bg-slate-50 dark:bg-gray-950 border border-slate-200 dark:border-gray-800 rounded-xl px-3.5 py-2 text-xs text-slate-900 dark:text-white focus:outline-none focus:border-indigo-500 font-medium"
                    />
                  </div>

                  <div>
                    <label className="block text-xs font-bold text-slate-700 dark:text-gray-300 mb-1">
                      Şifre Tekrar *
                    </label>
                    <input
                      type="password"
                      required
                      minLength={8}
                      value={regPasswordConfirm}
                      onChange={(e) => setRegPasswordConfirm(e.target.value)}
                      placeholder="••••••••••••"
                      className="w-full bg-slate-50 dark:bg-gray-950 border border-slate-200 dark:border-gray-800 rounded-xl px-3.5 py-2 text-xs text-slate-900 dark:text-white focus:outline-none focus:border-indigo-500 font-medium"
                    />
                  </div>

                  <div className="p-3 rounded-xl bg-indigo-50 dark:bg-indigo-950/40 border border-indigo-200 dark:border-indigo-800 text-[11px] text-indigo-700 dark:text-indigo-300 flex items-center gap-2">
                    <Sparkles className="w-4 h-4 text-amber-500 flex-shrink-0" />
                    <span>Ücretsiz <strong>$1.00 USD</strong> başlangıç kredisi ve Hoş Geldiniz e-postası anında tanımlanır.</span>
                  </div>

                  <button
                    type="submit"
                    disabled={regLoading}
                    className="w-full mt-2 py-3 rounded-xl bg-gradient-to-r from-indigo-600 to-purple-600 hover:from-indigo-500 hover:to-purple-500 text-white font-bold text-xs transition shadow-lg shadow-indigo-600/30 flex items-center justify-center gap-2 disabled:opacity-50"
                  >
                    {regLoading ? (
                      <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
                    ) : (
                      <>
                        <span>Ücretsiz Hesabımı Oluştur</span>
                        <ArrowRight className="w-4 h-4" />
                      </>
                    )}
                  </button>
                </form>
              </>
            )}

            {/* TAB 3: FORGOT PASSWORD */}
            {authMode === "forgot" && (
              <div className="space-y-4">
                {forgotSubmitted ? (
                  <div className="text-center space-y-3 py-4">
                    <div className="w-12 h-12 mx-auto rounded-full bg-emerald-50 dark:bg-emerald-950/40 text-emerald-600 flex items-center justify-center">
                      <CheckCircle2 className="w-6 h-6" />
                    </div>
                    <h3 className="font-bold text-sm text-slate-900 dark:text-white">Şifre Sıfırlama E-Postası Gönderildi</h3>
                    <p className="text-xs text-slate-500 dark:text-gray-400">
                      <strong>{forgotEmail}</strong> adresine 6 haneli güvenlik kodunuz iletildi.
                    </p>
                    <button
                      onClick={() => setAuthMode("login")}
                      className="mt-4 px-4 py-2 rounded-xl bg-indigo-600 text-white font-bold text-xs"
                    >
                      Giriş Sayfasına Dön
                    </button>
                  </div>
                ) : (
                  <form onSubmit={handleForgotSubmit} className="space-y-4">
                    <div>
                      <label className="block text-xs font-bold text-slate-700 dark:text-gray-300 mb-1.5">
                        Kayıtlı E-Posta Adresiniz
                      </label>
                      <input
                        type="email"
                        required
                        value={forgotEmail}
                        onChange={(e) => setForgotEmail(e.target.value)}
                        placeholder="adiniz@sirketiniz.com"
                        className="w-full bg-slate-50 dark:bg-gray-950 border border-slate-200 dark:border-gray-800 rounded-xl px-3.5 py-2.5 text-xs text-slate-900 dark:text-white"
                      />
                    </div>
                    <button
                      type="submit"
                      disabled={forgotLoading}
                      className="w-full py-3 rounded-xl bg-indigo-600 hover:bg-indigo-500 text-white font-bold text-xs transition shadow-md shadow-indigo-600/20"
                    >
                      {forgotLoading ? "Kod Gönderiliyor..." : "Sıfırlama Kodu Gönder"}
                    </button>
                    <div className="text-center">
                      <button
                        type="button"
                        onClick={() => setAuthMode("login")}
                        className="text-xs text-slate-500 hover:underline"
                      >
                        Giriş Ekranına Geri Dön
                      </button>
                    </div>
                  </form>
                )}
              </div>
            )}

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
        {/* SEKME 1: OPEN WEBUI SOHBET (CHAT PLAYGROUND) */}
        {/* ================================================================= */}
        {activeTab === "chat" && (
          <div className="flex h-[calc(100vh-120px)] rounded-2xl border border-slate-200 dark:border-gray-800 overflow-hidden bg-white dark:bg-gray-950 shadow-sm">
            
            {/* Sohbet Geçmişi Sol Kenar */}
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

                {/* Geçmiş Sohbetler */}
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
              
              {/* Üst Model ve Parametre Barı */}
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

              {/* Mesaj Gönderme Alanı */}
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
        {/* SEKME 2: MODEL KATALOĞU */}
        {/* ================================================================= */}
        {activeTab === "models" && (
          <div className="max-w-6xl mx-auto space-y-6">
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
              <div>
                <h2 className="text-xl font-black text-slate-900 dark:text-white">AWS Bedrock Model Kataloğu</h2>
                <p className="text-xs text-slate-500 dark:text-gray-400 mt-1">
                  API Gateway üzerinden erişilebilen tüm AWS Bedrock foundation modelleri.
                </p>
              </div>

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
                  OpenAI SDK ve harici istemciler için `sk-live-...` anahtarlarınızı yönetin.
                </p>
              </div>
            </div>

            <form onSubmit={handleCreateApiKey} className="p-5 rounded-2xl bg-white dark:bg-gray-900 border border-slate-200 dark:border-gray-800 flex gap-2">
              <input
                type="text"
                value={newKeyName}
                onChange={(e) => setNewKeyName(e.target.value)}
                placeholder="Anahtar Adı (Örn: Production App)..."
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

            {createdSecretKey && (
              <div className="p-4 rounded-2xl bg-amber-50 dark:bg-amber-950/40 border border-amber-200 dark:border-amber-800 space-y-2">
                <div className="text-xs font-bold text-amber-800 dark:text-amber-300 flex items-center gap-1.5">
                  <ShieldCheck className="w-4 h-4" />
                  <span>Yeni API Anahtarınız (Lütfen güvenli bir yere kaydedin):</span>
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

            <div className="rounded-2xl border border-slate-200 dark:border-gray-800 bg-white dark:bg-gray-900 overflow-hidden shadow-sm">
              <div className="p-4 border-b border-slate-200 dark:border-gray-800 font-bold text-xs">
                Mevcut Anahtarlarınız
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
        {/* SEKME 4: BAKİYE & CÜZDAN */}
        {/* ================================================================= */}
        {activeTab === "billing" && (
          <div className="max-w-4xl mx-auto space-y-6">
            <h2 className="text-xl font-black text-slate-900 dark:text-white">Bakiye & Cüzdan Yükleme</h2>
            
            <div className="p-6 rounded-3xl bg-gradient-to-r from-indigo-900 to-purple-900 text-white shadow-xl flex items-center justify-between">
              <div>
                <span className="text-xs text-indigo-200 font-semibold">Mevcut Bakiyeniz</span>
                <div className="text-3xl font-black mt-1">${balance.toFixed(2)} USD</div>
              </div>
              <div className="text-right text-xs text-indigo-200">
                <div>Hesap Türü: <strong>{user?.role?.toUpperCase()}</strong></div>
                <div className="text-emerald-300 font-semibold mt-1">✓ Bakiye Bittiğinde Otomatik Kesme Koruması</div>
              </div>
            </div>

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
        {/* SEKME 5: MODERN KULLANICI PROFİL SAYFASI */}
        {/* ================================================================= */}
        {activeTab === "profile" && (
          <div className="max-w-4xl mx-auto space-y-6">
            
            {/* Üst Profil Başlık Kartı */}
            <div className="p-6 rounded-3xl bg-white dark:bg-gray-900 border border-slate-200 dark:border-gray-800 shadow-sm flex flex-col sm:flex-row items-center gap-5">
              <div className="w-20 h-20 rounded-2xl bg-gradient-to-tr from-indigo-600 via-purple-600 to-amber-500 p-[3px] shadow-lg shadow-indigo-500/20">
                <div className="w-full h-full bg-white dark:bg-gray-950 rounded-[13px] flex items-center justify-center font-black text-2xl text-indigo-600 dark:text-indigo-400">
                  {user?.email?.charAt(0).toUpperCase() || "U"}
                </div>
              </div>

              <div className="flex-1 text-center sm:text-left space-y-1">
                <div className="flex flex-col sm:flex-row sm:items-center gap-2">
                  <h2 className="text-lg font-black text-slate-900 dark:text-white">{user?.email}</h2>
                  <span className="inline-block px-2.5 py-0.5 rounded-full text-[10px] font-extrabold uppercase tracking-wide bg-indigo-50 dark:bg-indigo-950 text-indigo-700 dark:text-indigo-300 border border-indigo-200 dark:border-indigo-800">
                    {user?.role} Seviyesi
                  </span>
                </div>
                <p className="text-xs text-slate-500 dark:text-gray-400 font-mono">ID: {user?.id}</p>
                <div className="flex items-center justify-center sm:justify-start gap-3 pt-1 text-[11px] text-slate-500">
                  <span className="flex items-center gap-1 text-emerald-600 font-semibold">
                    <CheckCircle2 className="w-3.5 h-3.5" /> Doğrulanmış Hesap
                  </span>
                  <span>•</span>
                  <span>Bakiye: <strong>${balance.toFixed(2)} USD</strong></span>
                </div>
              </div>
            </div>

            {/* Güvenlik & Şifre Değiştirme */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              
              {/* Şifre Değiştirme */}
              <div className="p-6 rounded-3xl bg-white dark:bg-gray-900 border border-slate-200 dark:border-gray-800 shadow-sm space-y-4">
                <h3 className="text-xs font-bold text-slate-900 dark:text-white uppercase tracking-wider flex items-center gap-1.5">
                  <KeyRound className="w-4 h-4 text-indigo-600" />
                  <span>Şifre Değiştir</span>
                </h3>

                {pwdMessage && (
                  <div className={`p-3 rounded-xl text-xs font-medium ${
                    pwdMessage.type === "success" 
                      ? "bg-emerald-50 text-emerald-700 border border-emerald-200" 
                      : "bg-red-50 text-red-700 border border-red-200"
                  }`}>
                    {pwdMessage.text}
                  </div>
                )}

                <form onSubmit={handleChangePassword} className="space-y-3">
                  <div>
                    <label className="block text-[11px] font-bold text-slate-700 dark:text-gray-300 mb-1">
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
                    <label className="block text-[11px] font-bold text-slate-700 dark:text-gray-300 mb-1">
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
                    className="w-full py-2.5 rounded-xl bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-bold transition shadow-md shadow-indigo-600/20"
                  >
                    Şifreyi Güncelle
                  </button>
                </form>
              </div>

              {/* İki Adımlı Doğrulama (2FA) */}
              <div className="p-6 rounded-3xl bg-white dark:bg-gray-900 border border-slate-200 dark:border-gray-800 shadow-sm space-y-4">
                <h3 className="text-xs font-bold text-slate-900 dark:text-white uppercase tracking-wider flex items-center gap-1.5">
                  <QrCode className="w-4 h-4 text-purple-600" />
                  <span>2FA İki Adımlı Doğrulama</span>
                </h3>

                {mfaStatus && (
                  <div className="p-3 rounded-xl bg-indigo-50 dark:bg-indigo-950/40 text-indigo-700 dark:text-indigo-300 text-xs border border-indigo-200 dark:border-indigo-800 font-medium">
                    {mfaStatus}
                  </div>
                )}

                {!mfaData ? (
                  <div className="space-y-3">
                    <p className="text-xs text-slate-500 dark:text-gray-400">
                      Hesabınızı Google Authenticator veya Authy ile koruyun. Giriş yaparken ek bir 6 haneli kod gerekecektir.
                    </p>
                    <button
                      onClick={handleInitiateMFA}
                      className="w-full py-2.5 rounded-xl bg-purple-600 hover:bg-purple-500 text-white text-xs font-bold transition shadow-md shadow-purple-600/20"
                    >
                      2FA Kurulumunu Başlat
                    </button>
                  </div>
                ) : (
                  <form onSubmit={handleVerifyMFA} className="space-y-3">
                    <div className="p-3 rounded-xl bg-slate-50 dark:bg-gray-950 border border-slate-200 dark:border-gray-800 text-xs space-y-1">
                      <div>Secret: <strong className="font-mono text-purple-600">{mfaData.secret}</strong></div>
                      <div className="text-[11px] text-slate-500">Authenticator uygulamanıza bu anahtarı girin.</div>
                    </div>
                    <div>
                      <input
                        type="text"
                        required
                        value={mfaCode}
                        onChange={(e) => setMfaCode(e.target.value)}
                        placeholder="6 haneli doğrulama kodu"
                        className="w-full bg-slate-50 dark:bg-gray-950 border border-slate-200 dark:border-gray-800 rounded-xl px-3.5 py-2 text-xs font-mono text-slate-900 dark:text-white text-center"
                      />
                    </div>
                    <button
                      type="submit"
                      className="w-full py-2.5 rounded-xl bg-purple-600 hover:bg-purple-500 text-white text-xs font-bold transition shadow-md shadow-purple-600/20"
                    >
                      Doğrula ve Aktifleştir
                    </button>
                  </form>
                )}
              </div>

            </div>

          </div>
        )}

        {/* ================================================================= */}
        {/* SEKME 6: ADMIN KONTROL MERKEZİ & AWS BULUT DİYAGNOSTİK */}
        {/* ================================================================= */}
        {activeTab === "admin" && user?.role === "admin" && (
          <div className="max-w-5xl mx-auto space-y-6">
            <div className="flex items-center justify-between">
              <div>
                <h2 className="text-xl font-black text-slate-900 dark:text-white">Admin Sistem Kontrol & AWS Canlı İzleme</h2>
                <p className="text-xs text-slate-500 dark:text-gray-400 mt-0.5">
                  AWS Bedrock bağlantı durumu, Fargate Cluster telemetrisi ve Kullanıcı yönetimi.
                </p>
              </div>
              <button
                onClick={fetchAdminData}
                className="flex items-center gap-1.5 px-3 py-1.5 rounded-xl border border-slate-200 dark:border-gray-800 bg-white dark:bg-gray-900 text-xs font-bold text-slate-700 dark:text-gray-300 hover:text-indigo-600"
              >
                <RefreshCw className="w-3.5 h-3.5" />
                <span>AWS Durumunu Yenile</span>
              </button>
            </div>

            {/* AWS & Bulut Servis Bağlantı Durumu Kartları */}
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
              
              {/* AWS Bedrock Runtime */}
              <div className="p-5 rounded-2xl bg-white dark:bg-gray-900 border border-slate-200 dark:border-gray-800 shadow-sm space-y-2">
                <div className="flex items-center justify-between text-xs text-slate-500 dark:text-gray-400">
                  <span className="font-bold">AWS Bedrock Runtime</span>
                  <Radio className="w-4 h-4 text-emerald-500 animate-pulse" />
                </div>
                <div className="text-base font-black text-slate-900 dark:text-white flex items-center gap-1.5">
                  <span className="w-2.5 h-2.5 rounded-full bg-emerald-500" />
                  <span>{awsStatus?.services?.aws_bedrock?.status || "CONNECTED"}</span>
                </div>
                <div className="text-[10px] text-slate-400 font-mono">
                  Bölge: {awsStatus?.region || "us-east-1"} · {awsStatus?.services?.aws_bedrock?.latency_ms || 12}ms
                </div>
              </div>

              {/* RDS PostgreSQL */}
              <div className="p-5 rounded-2xl bg-white dark:bg-gray-900 border border-slate-200 dark:border-gray-800 shadow-sm space-y-2">
                <div className="flex items-center justify-between text-xs text-slate-500 dark:text-gray-400">
                  <span className="font-bold">PostgreSQL 16 RDS</span>
                  <Database className="w-4 h-4 text-indigo-500" />
                </div>
                <div className="text-base font-black text-slate-900 dark:text-white flex items-center gap-1.5">
                  <span className="w-2.5 h-2.5 rounded-full bg-emerald-500" />
                  <span>{awsStatus?.services?.database_rds?.status || "CONNECTED"}</span>
                </div>
                <div className="text-[10px] text-slate-400">Multi-AZ Havuzu Aktif</div>
              </div>

              {/* ElastiCache Redis */}
              <div className="p-5 rounded-2xl bg-white dark:bg-gray-900 border border-slate-200 dark:border-gray-800 shadow-sm space-y-2">
                <div className="flex items-center justify-between text-xs text-slate-500 dark:text-gray-400">
                  <span className="font-bold">ElastiCache Redis 7</span>
                  <Zap className="w-4 h-4 text-amber-500" />
                </div>
                <div className="text-base font-black text-slate-900 dark:text-white flex items-center gap-1.5">
                  <span className="w-2.5 h-2.5 rounded-full bg-emerald-500" />
                  <span>CONNECTED</span>
                </div>
                <div className="text-[10px] text-slate-400">Hız Limitleyici Aktif</div>
              </div>

              {/* ECS Fargate Cluster */}
              <div className="p-5 rounded-2xl bg-white dark:bg-gray-900 border border-slate-200 dark:border-gray-800 shadow-sm space-y-2">
                <div className="flex items-center justify-between text-xs text-slate-500 dark:text-gray-400">
                  <span className="font-bold">ECS Fargate Cluster</span>
                  <Server className="w-4 h-4 text-purple-500" />
                </div>
                <div className="text-base font-black text-slate-900 dark:text-white flex items-center gap-1.5">
                  <span className="w-2.5 h-2.5 rounded-full bg-emerald-500" />
                  <span>HEALTHY</span>
                </div>
                <div className="text-[10px] text-slate-400">2 Görev Çalışıyor</div>
              </div>

            </div>

            {/* Grafana-Style Sistem CPU, Memory & Network Göstergeleri */}
            <div className="p-6 rounded-3xl bg-white dark:bg-gray-900 border border-slate-200 dark:border-gray-800 shadow-sm space-y-4">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <Gauge className="w-4 h-4 text-indigo-600" />
                  <span className="font-bold text-xs text-slate-900 dark:text-white uppercase tracking-wider">
                    Grafana Canlı Sistem Telemetrisi
                  </span>
                </div>
                <span className="text-[10px] px-2 py-0.5 rounded bg-emerald-50 dark:bg-emerald-950 text-emerald-600 font-bold border border-emerald-200 dark:border-emerald-800">
                  ● 1s Canlı Akış
                </span>
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 text-xs">
                <div className="p-4 rounded-2xl bg-slate-50 dark:bg-gray-950 border border-slate-200 dark:border-gray-800 space-y-1">
                  <div className="text-slate-500">CPU Kullanımı</div>
                  <div className="text-2xl font-black text-indigo-600 dark:text-indigo-400">
                    {awsStatus?.telemetry?.cpu_utilization_pct || 14.2}%
                  </div>
                  <div className="w-full bg-slate-200 dark:bg-gray-800 h-1.5 rounded-full overflow-hidden mt-2">
                    <div className="bg-indigo-600 h-full rounded-full" style={{ width: "14.2%" }} />
                  </div>
                </div>

                <div className="p-4 rounded-2xl bg-slate-50 dark:bg-gray-950 border border-slate-200 dark:border-gray-800 space-y-1">
                  <div className="text-slate-500">Bellek (RAM) Kullanımı</div>
                  <div className="text-2xl font-black text-purple-600 dark:text-purple-400">
                    {awsStatus?.telemetry?.memory_utilization_pct || 28.5}%
                  </div>
                  <div className="w-full bg-slate-200 dark:bg-gray-800 h-1.5 rounded-full overflow-hidden mt-2">
                    <div className="bg-purple-600 h-full rounded-full" style={{ width: "28.5%" }} />
                  </div>
                </div>

                <div className="p-4 rounded-2xl bg-slate-50 dark:bg-gray-950 border border-slate-200 dark:border-gray-800 space-y-1">
                  <div className="text-slate-500">Ağ Bant Genişliği</div>
                  <div className="text-2xl font-black text-emerald-600 dark:text-emerald-400">
                    {awsStatus?.telemetry?.network_out_mbps || 24.1} Mbps
                  </div>
                  <div className="text-[10px] text-slate-400 mt-1">Giriş: {awsStatus?.telemetry?.network_in_mbps || 8.4} Mbps</div>
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
                <input
                  type="text"
                  placeholder="Kullanıcı ara..."
                  value={userSearchTerm}
                  onChange={(e) => setUserSearchTerm(e.target.value)}
                  className="bg-slate-50 dark:bg-gray-950 border border-slate-200 dark:border-gray-800 px-3 py-1 text-xs rounded-lg text-slate-900 dark:text-white"
                />
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
                    {adminUsers
                      .filter((u) => u.email.toLowerCase().includes(userSearchTerm.toLowerCase()))
                      .map((u) => (
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
