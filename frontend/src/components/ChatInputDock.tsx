"use client";

import React, { useState, useRef, useEffect } from "react";
import {
  Send,
  Square,
  Paperclip,
  Mic,
  MicOff,
  Sparkles,
  FileText,
  Image as ImageIcon,
  Code,
  X,
  SlidersHorizontal,
  AtSign,
  Terminal,
  Cpu,
  Layers,
  CheckCircle,
} from "lucide-react";

export interface AttachedFile {
  id: string;
  name: string;
  type: string;
  size: number;
  tokensEstimate: number;
  previewUrl?: string;
  content?: string;
}

interface ChatInputDockProps {
  inputPrompt: string;
  setInputPrompt: (val: string) => void;
  onSendMessage: (files: AttachedFile[]) => void;
  isStreaming: boolean;
  onStopStreaming: () => void;
  selectedModel: string;
  onSelectModel: (modelId: string) => void;
  models: Array<{ id: string; name: string; type: string }>;
  onOpenSettings: () => void;
}

export default function ChatInputDock({
  inputPrompt,
  setInputPrompt,
  onSendMessage,
  isStreaming,
  onStopStreaming,
  selectedModel,
  onSelectModel,
  models,
  onOpenSettings,
}: ChatInputDockProps) {
  const [attachedFiles, setAttachedFiles] = useState<AttachedFile[]>([]);
  const [isRecording, setIsRecording] = useState(false);
  const [isDragOver, setIsDragOver] = useState(false);
  const [showMentionMenu, setShowMentionMenu] = useState(false);
  const [showSlashMenu, setShowSlashMenu] = useState(false);
  const [mentionQuery, setMentionQuery] = useState("");
  const [slashQuery, setSlashQuery] = useState("");
  const textareaRef = useRef<HTMLTextAreaElement>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  // Auto-resize textarea
  useEffect(() => {
    if (textareaRef.current) {
      textareaRef.current.style.height = "auto";
      textareaRef.current.style.height = `${Math.min(textareaRef.current.scrollHeight, 200)}px`;
    }
  }, [inputPrompt]);

  // Slash commands registry
  const slashCommands = [
    {
      cmd: "/canvas",
      label: "Canvas / Canlı UI",
      desc: "İnteraktif HTML, Tailwind veya Mermaid görsel bileşeni üret",
      prompt: "Lütfen interaktif ve modern bir arayüz bileşeni (HTML/Tailwind CSS) olarak Canvas'ta çalışacak şekilde kodla:\n",
    },
    {
      cmd: "/code",
      label: "Kod & Mimari",
      desc: "Tam ve hatasız production-ready kod blokları hazırla",
      prompt: "Lütfen aşağıdaki gereksinim için production-ready, clean-code standartlarında bir kod çözümü sağla:\n",
    },
    {
      cmd: "/summarize",
      label: "Akıllı Özet",
      desc: "Metni anahtar maddeler ve eylem adımlarıyla özetle",
      prompt: "Lütfen aşağıdaki metni yönetici özeti, kritik noktalar ve aksiyon maddeleri şeklinde özetle:\n",
    },
    {
      cmd: "/clear",
      label: "Bağlamı Sıfırla",
      desc: "Sohbet penceresindeki mevcut hafızayı sıfırla",
      prompt: "",
    },
  ];

  const handleInputChange = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
    const val = e.target.value;
    setInputPrompt(val);

    // Detect @ mention
    const lastAtIndex = val.lastIndexOf("@");
    if (lastAtIndex !== -1 && (lastAtIndex === 0 || val[lastAtIndex - 1] === " ")) {
      const q = val.slice(lastAtIndex + 1);
      if (!q.includes(" ")) {
        setShowMentionMenu(true);
        setMentionQuery(q.toLowerCase());
        setShowSlashMenu(false);
        return;
      }
    }
    setShowMentionMenu(false);

    // Detect / slash command
    if (val.startsWith("/")) {
      setShowSlashMenu(true);
      setSlashQuery(val.slice(1).toLowerCase());
    } else {
      setShowSlashMenu(false);
    }
  };

  const handleSelectMentionModel = (mId: string) => {
    onSelectModel(mId);
    // Replace @mention from input
    const lastAtIndex = inputPrompt.lastIndexOf("@");
    if (lastAtIndex !== -1) {
      setInputPrompt(inputPrompt.slice(0, lastAtIndex));
    }
    setShowMentionMenu(false);
    textareaRef.current?.focus();
  };

  const handleSelectSlashCommand = (cmd: (typeof slashCommands)[0]) => {
    setInputPrompt(cmd.prompt);
    setShowSlashMenu(false);
    textareaRef.current?.focus();
  };

  const handleFileUpload = (e: React.ChangeEvent<HTMLInputElement>) => {
    const files = e.target.files;
    if (!files || files.length === 0) return;
    processFiles(Array.from(files));
  };

  const processFiles = (files: File[]) => {
    files.forEach((file) => {
      const isImg = file.type.startsWith("image/");
      const tokens = Math.ceil(file.size / 4);
      const reader = new FileReader();

      reader.onload = (event) => {
        const content = event.target?.result as string;
        const newAttachment: AttachedFile = {
          id: Math.random().toString(36).substring(7),
          name: file.name,
          type: file.type || "application/octet-stream",
          size: file.size,
          tokensEstimate: tokens,
          previewUrl: isImg ? content : undefined,
          content: content,
        };
        setAttachedFiles((prev) => [...prev, newAttachment]);
      };

      if (isImg) {
        reader.readAsDataURL(file);
      } else {
        reader.readAsText(file);
      }
    });
  };

  const handleRemoveFile = (id: string) => {
    setAttachedFiles((prev) => prev.filter((f) => f.id !== id));
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      if (!isStreaming && (inputPrompt.trim() || attachedFiles.length > 0)) {
        onSendMessage(attachedFiles);
        setAttachedFiles([]);
      }
    }
  };

  const toggleVoiceRecording = () => {
    if (isRecording) {
      setIsRecording(false);
    } else {
      setIsRecording(true);
      // Simulate speech recognition transcription placeholder
      setTimeout(() => {
        const appended = inputPrompt ? `${inputPrompt} AWS Bedrock modellerini karşılaştır.` : "AWS Bedrock modellerini karşılaştır.";
        setInputPrompt(appended);
        setIsRecording(false);
      }, 3000);

    }
  };

  return (
    <div
      className="relative w-full max-w-4xl mx-auto"
      onDragOver={(e) => {
        e.preventDefault();
        setIsDragOver(true);
      }}
      onDragLeave={() => setIsDragOver(false)}
      onDrop={(e) => {
        e.preventDefault();
        setIsDragOver(false);
        if (e.dataTransfer.files) {
          processFiles(Array.from(e.dataTransfer.files));
        }
      }}
    >
      {/* Drag & Drop Overlay */}
      {isDragOver && (
        <div className="absolute inset-0 z-30 rounded-3xl bg-indigo-600/90 backdrop-blur-md border-2 border-dashed border-white flex flex-col items-center justify-center text-white space-y-2 pointer-events-none">
          <Paperclip className="w-8 h-8 animate-bounce" />
          <p className="font-black text-sm">Dosyayı Bırakın (PDF, CSV, Kod, Görsel)</p>
        </div>
      )}

      {/* @ Mention Model Popover */}
      {showMentionMenu && (
        <div className="absolute bottom-full mb-2 left-0 w-80 max-h-60 overflow-y-auto rounded-2xl bg-white dark:bg-gray-900 border border-slate-200 dark:border-gray-800 shadow-2xl z-40 p-2 space-y-1">
          <div className="px-3 py-1.5 text-[10px] font-bold uppercase tracking-wider text-slate-400 flex items-center gap-1.5 border-b border-slate-100 dark:border-gray-800">
            <AtSign className="w-3 h-3 text-indigo-600" />
            <span>Model veya Bağlam Seç</span>
          </div>
          {models
            .filter((m) => m.name.toLowerCase().includes(mentionQuery) || m.id.toLowerCase().includes(mentionQuery))
            .map((m) => (
              <button
                key={m.id}
                type="button"
                onClick={() => handleSelectMentionModel(m.id)}
                className="w-full px-3 py-2 rounded-xl text-left hover:bg-indigo-50 dark:hover:bg-gray-800 flex items-center justify-between transition group"
              >
                <div>
                  <div className="text-xs font-bold text-slate-900 dark:text-white group-hover:text-indigo-600">
                    {m.name}
                  </div>
                  <div className="text-[10px] text-slate-400 font-mono">{m.id}</div>
                </div>
                <span className="text-[9px] px-1.5 py-0.5 rounded bg-slate-100 dark:bg-gray-800 text-slate-600 dark:text-gray-300 font-bold">
                  {m.type}
                </span>
              </button>
            ))}
        </div>
      )}

      {/* / Slash Command Popover */}
      {showSlashMenu && (
        <div className="absolute bottom-full mb-2 left-0 w-96 max-h-64 overflow-y-auto rounded-2xl bg-white dark:bg-gray-900 border border-slate-200 dark:border-gray-800 shadow-2xl z-40 p-2 space-y-1">
          <div className="px-3 py-1.5 text-[10px] font-bold uppercase tracking-wider text-slate-400 flex items-center gap-1.5 border-b border-slate-100 dark:border-gray-800">
            <Terminal className="w-3 h-3 text-purple-600" />
            <span>Hızlı Komutlar</span>
          </div>
          {slashCommands
            .filter((c) => c.cmd.includes(slashQuery) || c.label.toLowerCase().includes(slashQuery))
            .map((c) => (
              <button
                key={c.cmd}
                type="button"
                onClick={() => handleSelectSlashCommand(c)}
                className="w-full px-3 py-2 rounded-xl text-left hover:bg-purple-50 dark:hover:bg-gray-800 flex items-start gap-2.5 transition group"
              >
                <div className="w-6 h-6 rounded-lg bg-purple-100 dark:bg-purple-950 text-purple-600 flex items-center justify-center shrink-0 mt-0.5 font-mono text-xs font-black">
                  /
                </div>
                <div>
                  <div className="text-xs font-bold text-slate-900 dark:text-white group-hover:text-purple-600">
                    {c.cmd} <span className="font-normal text-slate-500">({c.label})</span>
                  </div>
                  <div className="text-[11px] text-slate-400">{c.desc}</div>
                </div>
              </button>
            ))}
        </div>
      )}

      {/* Main Input Dock Container */}
      <div className="rounded-3xl border border-slate-200/90 dark:border-gray-800 bg-white/95 dark:bg-gray-900/95 backdrop-blur-xl shadow-2xl shadow-indigo-950/10 dark:shadow-black/50 p-3 space-y-2">
        {/* Attached Files Chips */}
        {attachedFiles.length > 0 && (
          <div className="flex flex-wrap items-center gap-2 px-2 pt-1 pb-2 border-b border-slate-100 dark:border-gray-800">
            {attachedFiles.map((file) => (
              <div
                key={file.id}
                className="flex items-center gap-2 pl-2 pr-1.5 py-1 rounded-xl bg-slate-100 dark:bg-gray-800 border border-slate-200 dark:border-gray-700 text-xs font-medium"
              >
                {file.previewUrl ? (
                  <img src={file.previewUrl} alt="Preview" className="w-5 h-5 rounded-md object-cover" />
                ) : (
                  <FileText className="w-3.5 h-3.5 text-indigo-500" />
                )}
                <span className="max-w-[140px] truncate font-bold text-slate-800 dark:text-gray-200">
                  {file.name}
                </span>
                <span className="text-[10px] text-slate-400 font-mono">~{file.tokensEstimate}t</span>
                <button
                  type="button"
                  onClick={() => handleRemoveFile(file.id)}
                  className="p-1 rounded-lg hover:bg-slate-200 dark:hover:bg-gray-700 text-slate-400 hover:text-red-500 transition"
                >
                  <X className="w-3 h-3" />
                </button>
              </div>
            ))}
          </div>
        )}

        {/* Text Input Area */}
        <div className="flex items-start gap-2 px-2">
          <textarea
            ref={textareaRef}
            rows={1}
            value={inputPrompt}
            onChange={handleInputChange}
            onKeyDown={handleKeyDown}
            placeholder="Bir soru sorun, '@' ile model seçin, '/' ile Canvas üretin veya dosya sürükleyin..."
            className="w-full bg-transparent border-none outline-none resize-none text-xs sm:text-sm text-slate-900 dark:text-white placeholder-slate-400 dark:placeholder-gray-500 leading-relaxed py-1.5 max-h-48"
          />
        </div>

        {/* Toolbar & Actions Bottom Row */}
        <div className="flex items-center justify-between pt-1 border-t border-slate-100 dark:border-gray-800/80">
          <div className="flex items-center gap-1.5">
            <input
              type="file"
              ref={fileInputRef}
              onChange={handleFileUpload}
              multiple
              className="hidden"
              accept=".pdf,.csv,.txt,.json,.py,.ts,.tsx,.js,.png,.jpg,.jpeg,.webp"
            />
            <button
              type="button"
              onClick={() => fileInputRef.current?.click()}
              title="Dosya veya Görsel Ekle"
              className="p-2 rounded-xl text-slate-500 hover:text-slate-900 dark:hover:text-white hover:bg-slate-100 dark:hover:bg-gray-800 transition"
            >
              <Paperclip className="w-4 h-4" />
            </button>

            <button
              type="button"
              onClick={toggleVoiceRecording}
              title={isRecording ? "Kaydı Durdur" : "Sesli Giriş"}
              className={`p-2 rounded-xl transition ${
                isRecording
                  ? "bg-red-500 text-white animate-pulse"
                  : "text-slate-500 hover:text-slate-900 dark:hover:text-white hover:bg-slate-100 dark:hover:bg-gray-800"
              }`}
            >
              {isRecording ? <MicOff className="w-4 h-4" /> : <Mic className="w-4 h-4" />}
            </button>

            <button
              type="button"
              onClick={onOpenSettings}
              title="Model Parametreleri (Temperature, Prompt)"
              className="p-2 rounded-xl text-slate-500 hover:text-slate-900 dark:hover:text-white hover:bg-slate-100 dark:hover:bg-gray-800 transition flex items-center gap-1 text-xs font-semibold"
            >
              <SlidersHorizontal className="w-3.5 h-3.5" />
            </button>

            {/* Current Model Badge */}
            <div className="hidden sm:flex items-center gap-1.5 px-2.5 py-1 rounded-xl bg-slate-100 dark:bg-gray-800/80 border border-slate-200 dark:border-gray-700 text-[11px] font-bold text-slate-700 dark:text-gray-300">
              <Cpu className="w-3.5 h-3.5 text-indigo-500" />
              <span className="max-w-[120px] truncate">{selectedModel.split("/").pop() || selectedModel}</span>
            </div>
          </div>

          <div className="flex items-center gap-2">
            {isStreaming ? (
              <button
                type="button"
                onClick={onStopStreaming}
                className="flex items-center gap-1.5 px-3.5 py-2 rounded-2xl bg-red-600 hover:bg-red-500 text-white font-bold text-xs shadow-md shadow-red-600/20 transition"
              >
                <Square className="w-3.5 h-3.5 fill-current" />
                <span>Durdur</span>
              </button>
            ) : (
              <button
                type="button"
                onClick={() => {
                  if (inputPrompt.trim() || attachedFiles.length > 0) {
                    onSendMessage(attachedFiles);
                    setAttachedFiles([]);
                  }
                }}
                disabled={!inputPrompt.trim() && attachedFiles.length === 0}
                className="p-2.5 rounded-2xl bg-indigo-600 hover:bg-indigo-500 disabled:opacity-30 text-white font-bold shadow-md shadow-indigo-600/20 transition"
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
