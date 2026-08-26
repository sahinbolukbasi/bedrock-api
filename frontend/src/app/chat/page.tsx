"use client";

import React, { useState, useEffect, useRef } from "react";
import { 
  Send, 
  Square, 
  Sparkles, 
  Settings2, 
  Trash2, 
  Copy, 
  Check, 
  Cpu, 
  User as UserIcon, 
  Bot, 
  Coins,
  ChevronDown
} from "lucide-react";
import { API_BASE, getAuthToken, fetchApi } from "../../lib/api";
import AuthGuard from "../../components/AuthGuard";

interface Message {
  id: string;
  role: "user" | "assistant" | "system";
  content: string;
  tokens?: number;
  cost?: number;
}

export default function ChatPlayground() {
  return (
    <AuthGuard>
      <ChatPlaygroundContent />
    </AuthGuard>
  );
}

function ChatPlaygroundContent() {
  const [messages, setMessages] = useState<Message[]>([
    {
      id: "1",
      role: "assistant",
      content: "Hello! I am connected to **AWS Bedrock**. Select your desired foundation model from the header to begin streaming inference.",
    },
  ]);
  const [input, setInput] = useState("");
  const [isStreaming, setIsStreaming] = useState(false);
  const [model, setModel] = useState("anthropic.claude-3-5-sonnet-20241022-v2:0");
  const [modelsList, setModelsList] = useState<any[]>([]);
  const [temperature, setTemperature] = useState(0.7);
  const [systemPrompt, setSystemPrompt] = useState("You are an expert AI software engineer and architect.");
  const [showSettings, setShowSettings] = useState(false);
  const [copiedId, setCopiedId] = useState<string | null>(null);

  const messagesEndRef = useRef<HTMLDivElement>(null);
  const abortControllerRef = useRef<AbortController | null>(null);

  useEffect(() => {
    async function loadModels() {
      try {
        const res = await fetchApi("/v1/models");
        if (res.data) setModelsList(res.data);
      } catch (err) {
        console.error("Failed to load models:", err);
      }
    }
    loadModels();
  }, []);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  const handleCopy = (text: string, id: string) => {
    navigator.clipboard.writeText(text);
    setCopiedId(id);
    setTimeout(() => setCopiedId(null), 2000);
  };

  const handleSendMessage = async () => {
    if (!input.trim() || isStreaming) return;

    const userMessage: Message = {
      id: Date.now().toString(),
      role: "user",
      content: input.trim(),
    };

    const assistantPlaceholder: Message = {
      id: (Date.now() + 1).toString(),
      role: "assistant",
      content: "",
    };

    const newMessages = [...messages, userMessage];
    setMessages([...newMessages, assistantPlaceholder]);
    setInput("");
    setIsStreaming(true);

    const token = getAuthToken();
    const headers: Record<string, string> = {
      "Content-Type": "application/json",
    };
    if (token) headers["Authorization"] = `Bearer ${token}`;

    abortControllerRef.current = new AbortController();

    try {
      const payloadMessages = [
        ...(systemPrompt ? [{ role: "system", content: systemPrompt }] : []),
        ...newMessages.map((m) => ({ role: m.role, content: m.content })),
      ];

      const response = await fetch(`${API_BASE}/v1/chat/completions`, {
        method: "POST",
        headers,
        body: JSON.stringify({
          model,
          messages: payloadMessages,
          temperature,
          stream: true,
        }),
        signal: abortControllerRef.current.signal,
      });

      if (!response.ok) {
        const err = await response.json().catch(() => ({}));
        throw new Error(err?.error?.message || "Failed to stream completion.");
      }

      const reader = response.body?.getReader();
      const decoder = new TextDecoder();
      let accumulatedText = "";

      if (reader) {
        while (true) {
          const { done, value } = await reader.read();
          if (done) break;

          const chunk = decoder.decode(value, { stream: true });
          const lines = chunk.split("\n");

          for (const line of lines) {
            if (line.startsWith("data: ")) {
              const dataStr = line.replace("data: ", "").trim();
              if (dataStr === "[DONE]") continue;

              try {
                const parsed = JSON.parse(dataStr);
                const delta = parsed.choices?.[0]?.delta?.content || "";
                accumulatedText += delta;

                setMessages((prev) => {
                  const updated = [...prev];
                  const last = updated[updated.length - 1];
                  if (last && last.role === "assistant") {
                    last.content = accumulatedText;
                    last.tokens = Math.max(10, Math.floor(accumulatedText.length / 3));
                    last.cost = Number(((last.tokens / 1000) * 0.018).toFixed(6));
                  }
                  return updated;
                });
              } catch (e) {
                // Ignore parse errors on partial chunks
              }
            }
          }
        }
      }
    } catch (err: any) {
      if (err.name !== "AbortError") {
        setMessages((prev) => {
          const updated = [...prev];
          const last = updated[updated.length - 1];
          if (last) {
            last.content = `⚠️ **Error**: ${err.message || "An unexpected error occurred."}`;
          }
          return updated;
        });
      }
    } finally {
      setIsStreaming(false);
      abortControllerRef.current = null;
    }
  };

  const handleStopGeneration = () => {
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
      setIsStreaming(false);
    }
  };

  const handleClearChat = () => {
    setMessages([
      {
        id: Date.now().toString(),
        role: "assistant",
        content: "Chat cleared. What model or prompt would you like to test next?",
      },
    ]);
  };

  return (
    <div className="flex h-[calc(100vh-4rem)] bg-background">
      {/* Main Chat Area */}
      <div className="flex-1 flex flex-col max-w-5xl mx-auto w-full px-4 py-4">
        
        {/* Top Control Bar */}
        <div className="flex items-center justify-between border-b border-gray-800 pb-3 mb-4">
          <div className="flex items-center gap-3">
            <div className="relative">
              <select
                value={model}
                onChange={(e) => setModel(e.target.value)}
                className="appearance-none bg-gray-900 border border-gray-800 text-white text-xs font-semibold py-2 pl-3 pr-8 rounded-xl focus:outline-none focus:border-indigo-500 transition cursor-pointer"
              >
                {modelsList.length > 0 ? (
                  modelsList.map((m) => (
                    <option key={m.id} value={m.id}>
                      {m.name || m.id}
                    </option>
                  ))
                ) : (
                  <>
                    <option value="anthropic.claude-3-5-sonnet-20241022-v2:0">Claude 3.5 Sonnet v2</option>
                    <option value="amazon.nova-pro-v1:0">Amazon Nova Pro</option>
                    <option value="amazon.nova-lite-v1:0">Amazon Nova Lite</option>
                    <option value="meta.llama3-3-70b-instruct-v1:0">Meta Llama 3.3 70B</option>
                  </>
                )}
              </select>
              <ChevronDown className="w-3.5 h-3.5 text-gray-400 absolute right-2.5 top-1/2 -translate-y-1/2 pointer-events-none" />
            </div>

            <span className="text-[11px] text-gray-500 font-mono hidden sm:inline">
              AWS Bedrock Region: us-east-1
            </span>
          </div>

          <div className="flex items-center gap-2">
            <button
              onClick={() => setShowSettings(!showSettings)}
              className={`p-2 rounded-lg text-xs font-medium border transition flex items-center gap-1.5 ${
                showSettings ? "bg-indigo-600/20 text-indigo-400 border-indigo-500/40" : "bg-gray-900 border-gray-800 text-gray-400 hover:text-white"
              }`}
            >
              <Settings2 className="w-3.5 h-3.5" /> Params
            </button>
            <button
              onClick={handleClearChat}
              className="p-2 rounded-lg text-xs font-medium bg-gray-900 border border-gray-800 text-gray-400 hover:text-red-400 transition"
              title="Clear Conversation"
            >
              <Trash2 className="w-3.5 h-3.5" />
            </button>
          </div>
        </div>

        {/* Parameter Drawer */}
        {showSettings && (
          <div className="mb-4 p-4 rounded-xl bg-gray-900/90 border border-gray-800 text-xs grid grid-cols-1 md:grid-cols-2 gap-4 animate-in fade-in duration-200">
            <div>
              <label className="block text-gray-300 font-medium mb-1">System Prompt</label>
              <textarea
                value={systemPrompt}
                onChange={(e) => setSystemPrompt(e.target.value)}
                rows={2}
                className="w-full bg-gray-950 border border-gray-800 rounded-lg p-2 text-gray-300 focus:outline-none focus:border-indigo-500 resize-none font-mono"
              />
            </div>
            <div>
              <div className="flex justify-between text-gray-300 font-medium mb-1">
                <span>Temperature</span>
                <span className="font-mono text-indigo-400">{temperature}</span>
              </div>
              <input
                type="range"
                min="0"
                max="1"
                step="0.05"
                value={temperature}
                onChange={(e) => setTemperature(parseFloat(e.target.value))}
                className="w-full accent-indigo-500 cursor-pointer"
              />
              <span className="text-[10px] text-gray-500 mt-1 block">
                Lower values are deterministic; higher values are more creative.
              </span>
            </div>
          </div>
        )}

        {/* Message Thread */}
        <div className="flex-1 overflow-y-auto space-y-4 pr-2">
          {messages.map((m) => {
            const isUser = m.role === "user";
            return (
              <div
                key={m.id}
                className={`flex gap-3 text-sm ${isUser ? "justify-end" : "justify-start"}`}
              >
                {!isUser && (
                  <div className="w-8 h-8 rounded-lg bg-indigo-950 border border-indigo-800/60 flex items-center justify-center text-indigo-400 shrink-0 mt-0.5">
                    <Bot className="w-4 h-4" />
                  </div>
                )}

                <div className={`max-w-[82%] rounded-2xl px-4 py-3 relative group ${
                  isUser 
                    ? "bg-indigo-600 text-white rounded-br-none" 
                    : "bg-gray-900/80 border border-gray-800 text-gray-200 rounded-bl-none"
                }`}>
                  <div className="whitespace-pre-wrap leading-relaxed font-sans">
                    {m.content || (isStreaming && <span className="inline-block animate-pulse">▋</span>)}
                  </div>

                  {/* Message Meta / Badges */}
                  {!isUser && m.tokens && (
                    <div className="mt-2.5 pt-2 border-t border-gray-800/80 flex items-center justify-between text-[11px] text-gray-500 font-mono">
                      <div className="flex items-center gap-3">
                        <span>{m.tokens} tokens</span>
                        {m.cost !== undefined && (
                          <span className="text-emerald-400/90 font-semibold">${m.cost.toFixed(5)}</span>
                        )}
                      </div>
                      <button
                        onClick={() => handleCopy(m.content, m.id)}
                        className="opacity-0 group-hover:opacity-100 transition text-gray-400 hover:text-white flex items-center gap-1"
                      >
                        {copiedId === m.id ? <Check className="w-3 h-3 text-emerald-400" /> : <Copy className="w-3 h-3" />}
                        <span>{copiedId === m.id ? "Copied" : "Copy"}</span>
                      </button>
                    </div>
                  )}
                </div>

                {isUser && (
                  <div className="w-8 h-8 rounded-lg bg-gray-800 flex items-center justify-center text-gray-300 shrink-0 mt-0.5">
                    <UserIcon className="w-4 h-4" />
                  </div>
                )}
              </div>
            );
          })}
          <div ref={messagesEndRef} />
        </div>

        {/* Input Bar */}
        <div className="mt-3 relative">
          <div className="flex items-center rounded-2xl bg-gray-900 border border-gray-800 focus-within:border-indigo-500 transition p-1.5 shadow-xl">
            <textarea
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === "Enter" && !e.shiftKey) {
                  e.preventDefault();
                  handleSendMessage();
                }
              }}
              placeholder={`Message ${model.split(".")[1]?.split("-")[0] || "Bedrock"} (Shift + Enter for new line)...`}
              rows={1}
              className="flex-1 bg-transparent border-0 px-3 py-2 text-sm text-gray-200 placeholder-gray-500 focus:outline-none resize-none"
            />

            {isStreaming ? (
              <button
                onClick={handleStopGeneration}
                className="p-2.5 rounded-xl bg-red-600 hover:bg-red-500 text-white font-medium transition flex items-center gap-1.5 text-xs shadow-md"
              >
                <Square className="w-3.5 h-3.5 fill-current" /> Stop
              </button>
            ) : (
              <button
                onClick={handleSendMessage}
                disabled={!input.trim()}
                className="p-2.5 rounded-xl bg-indigo-600 hover:bg-indigo-500 disabled:opacity-40 disabled:hover:bg-indigo-600 text-white transition shadow-md shadow-indigo-600/30"
              >
                <Send className="w-4 h-4" />
              </button>
            )}
          </div>
        </div>

      </div>
    </div>
  );
}
