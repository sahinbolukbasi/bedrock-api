"use client";

import React, { useState, useEffect, useRef } from "react";
import {
  X,
  Code2,
  Eye,
  Download,
  Copy,
  Check,
  Maximize2,
  Minimize2,
  Sparkles,
  RefreshCw,
  Layers,
  FileCode,
  CheckCircle2,
} from "lucide-react";

export interface ArtifactData {
  id: string;
  title: string;
  type: "html" | "react" | "svg" | "mermaid" | "code" | "json_form";
  content: string;
  language?: string;
}

interface ArtifactCanvasProps {
  isOpen: boolean;
  onClose: () => void;
  artifact: ArtifactData | null;
}

export default function ArtifactCanvas({ isOpen, onClose, artifact }: ArtifactCanvasProps) {
  const [activeTab, setActiveTab] = useState<"preview" | "code">("preview");
  const [copied, setCopied] = useState(false);
  const [isFullscreen, setIsFullscreen] = useState(false);
  const [refreshKey, setRefreshKey] = useState(0);
  const iframeRef = useRef<HTMLIFrameElement>(null);

  useEffect(() => {
    if (artifact) {
      setActiveTab(artifact.type === "code" ? "code" : "preview");
    }
  }, [artifact]);

  if (!isOpen || !artifact) return null;

  const handleCopy = () => {
    navigator.clipboard.writeText(artifact.content);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const handleDownload = () => {
    let extension = ".txt";
    let mimeType = "text/plain";

    if (artifact.type === "html") {
      extension = ".html";
      mimeType = "text/html";
    } else if (artifact.type === "svg") {
      extension = ".svg";
      mimeType = "image/svg+xml";
    } else if (artifact.type === "mermaid") {
      extension = ".mmd";
    } else if (artifact.type === "json_form") {
      extension = ".json";
      mimeType = "application/json";
    } else if (artifact.language === "python" || artifact.language === "py") {
      extension = ".py";
    } else if (artifact.language === "typescript" || artifact.language === "ts" || artifact.language === "tsx") {
      extension = ".tsx";
    } else if (artifact.language === "javascript" || artifact.language === "js") {
      extension = ".js";
    }

    const filename = `${artifact.title.toLowerCase().replace(/[^a-z0-9]/g, "_")}${extension}`;
    const blob = new Blob([artifact.content], { type: mimeType });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = filename;
    a.click();
    URL.revokeObjectURL(url);
  };

  const generateIframeHtml = () => {
    if (artifact.type === "html" || artifact.type === "react") {
      return `
        <!DOCTYPE html>
        <html lang="tr">
          <head>
            <meta charset="UTF-8" />
            <meta name="viewport" content="width=device-width, initial-scale=1.0" />
            <script src="https://cdn.tailwindcss.com"></script>
            <link href="https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&family=JetBrains+Mono:wght@400;500;700&display=swap" rel="stylesheet">
            <style>
              body {
                font-family: 'Plus Jakarta Sans', -apple-system, BlinkMacSystemFont, sans-serif;
                margin: 0;
                padding: 16px;
                background-color: #090d16;
                color: #f8fafc;
              }
            </style>
          </head>
          <body>
            ${artifact.content}
          </body>
        </html>
      `;
    }
    return "";
  };

  return (
    <aside
      className={`fixed top-16 right-0 bottom-0 z-40 bg-white dark:bg-gray-950 border-l border-slate-200 dark:border-gray-800 shadow-2xl flex flex-col transition-all duration-300 ${
        isFullscreen ? "w-full md:w-full z-50 top-0" : "w-full md:w-[48%] lg:w-[42%]"
      }`}
    >
      {/* Canvas Top Bar */}
      <div className="h-14 px-4 border-b border-slate-200 dark:border-gray-800 flex items-center justify-between bg-slate-50/80 dark:bg-gray-900/80 backdrop-blur-md">
        <div className="flex items-center gap-2.5 min-w-0">
          <div className="w-8 h-8 rounded-xl bg-gradient-to-tr from-indigo-600 to-purple-600 flex items-center justify-center text-white shadow-md shadow-indigo-600/20 shrink-0">
            <Layers className="w-4 h-4" />
          </div>
          <div className="min-w-0">
            <div className="flex items-center gap-2">
              <h3 className="font-bold text-xs text-slate-900 dark:text-white truncate">
                {artifact.title || "Dinamik Canvas Bileşeni"}
              </h3>
              <span className="text-[9px] uppercase px-1.5 py-0.5 rounded font-black tracking-wider bg-indigo-50 dark:bg-indigo-950 text-indigo-600 dark:text-indigo-400 border border-indigo-200 dark:border-indigo-800">
                {artifact.type}
              </span>
            </div>
            <p className="text-[10px] text-slate-400 font-mono truncate">
              {artifact.language || "interactive-runtime"}
            </p>
          </div>
        </div>

        {/* Tab & Action Controls */}
        <div className="flex items-center gap-1.5">
          {artifact.type !== "code" && (
            <div className="flex items-center p-0.5 rounded-lg bg-slate-200/80 dark:bg-gray-800 mr-2">
              <button
                onClick={() => setActiveTab("preview")}
                className={`flex items-center gap-1 px-2.5 py-1 rounded-md text-[11px] font-bold transition ${
                  activeTab === "preview"
                    ? "bg-white dark:bg-gray-900 text-indigo-600 dark:text-indigo-400 shadow-sm"
                    : "text-slate-600 dark:text-gray-400 hover:text-slate-900"
                }`}
              >
                <Eye className="w-3 h-3" />
                <span>Önizleme</span>
              </button>
              <button
                onClick={() => setActiveTab("code")}
                className={`flex items-center gap-1 px-2.5 py-1 rounded-md text-[11px] font-bold transition ${
                  activeTab === "code"
                    ? "bg-white dark:bg-gray-900 text-indigo-600 dark:text-indigo-400 shadow-sm"
                    : "text-slate-600 dark:text-gray-400 hover:text-slate-900"
                }`}
              >
                <Code2 className="w-3 h-3" />
                <span>Kod</span>
              </button>
            </div>
          )}

          {activeTab === "preview" && (artifact.type === "html" || artifact.type === "react") && (
            <button
              onClick={() => setRefreshKey((k) => k + 1)}
              title="Yeniden Yükle"
              className="p-1.5 rounded-lg hover:bg-slate-200 dark:hover:bg-gray-800 text-slate-500 hover:text-slate-900 dark:hover:text-white transition"
            >
              <RefreshCw className="w-3.5 h-3.5" />
            </button>
          )}

          <button
            onClick={handleCopy}
            title="Kodu Kopyala"
            className="p-1.5 rounded-lg hover:bg-slate-200 dark:hover:bg-gray-800 text-slate-500 hover:text-slate-900 dark:hover:text-white transition"
          >
            {copied ? <Check className="w-3.5 h-3.5 text-emerald-500" /> : <Copy className="w-3.5 h-3.5" />}
          </button>

          <button
            onClick={handleDownload}
            title="Dosyayı İndir"
            className="p-1.5 rounded-lg hover:bg-slate-200 dark:hover:bg-gray-800 text-slate-500 hover:text-slate-900 dark:hover:text-white transition"
          >
            <Download className="w-3.5 h-3.5" />
          </button>

          <button
            onClick={() => setIsFullscreen(!isFullscreen)}
            title={isFullscreen ? "Küçült" : "Tam Ekran"}
            className="p-1.5 rounded-lg hover:bg-slate-200 dark:hover:bg-gray-800 text-slate-500 hover:text-slate-900 dark:hover:text-white transition"
          >
            {isFullscreen ? <Minimize2 className="w-3.5 h-3.5" /> : <Maximize2 className="w-3.5 h-3.5" />}
          </button>

          <button
            onClick={onClose}
            title="Kapat"
            className="p-1.5 rounded-lg hover:bg-red-50 dark:hover:bg-red-950 text-slate-400 hover:text-red-600 transition"
          >
            <X className="w-4 h-4" />
          </button>
        </div>
      </div>

      {/* Canvas Body Viewport */}
      <div className="flex-1 overflow-hidden relative bg-slate-100 dark:bg-gray-950">
        {activeTab === "preview" ? (
          <div className="w-full h-full flex flex-col">
            {/* HTML / React Sandbox */}
            {(artifact.type === "html" || artifact.type === "react") && (
              <iframe
                key={refreshKey}
                ref={iframeRef}
                title="Artifact Sandbox"
                srcDoc={generateIframeHtml()}
                sandbox="allow-scripts allow-modals allow-forms allow-popups"
                className="w-full h-full border-none bg-slate-950"
              />
            )}

            {/* SVG Visualizer */}
            {artifact.type === "svg" && (
              <div
                className="w-full h-full flex items-center justify-center p-8 overflow-auto bg-slate-950"
                dangerouslySetInnerHTML={{ __html: artifact.content }}
              />
            )}

            {/* Mermaid Diagram Viewer */}
            {artifact.type === "mermaid" && (
              <div className="w-full h-full p-6 overflow-auto bg-slate-900 text-slate-100 flex flex-col items-center justify-center">
                <div className="p-4 rounded-2xl bg-gray-950 border border-gray-800 w-full max-w-lg shadow-xl text-xs font-mono whitespace-pre-wrap">
                  <div className="flex items-center gap-2 text-indigo-400 font-bold mb-3 pb-2 border-b border-gray-800">
                    <Sparkles className="w-4 h-4" /> Mermaid.js Diagram Tanımı
                  </div>
                  {artifact.content}
                </div>
              </div>
            )}

            {/* OpenUI Dynamic JSON Form */}
            {artifact.type === "json_form" && (
              <div className="w-full h-full p-6 overflow-auto bg-slate-900">
                <div className="max-w-md mx-auto p-6 rounded-3xl bg-gray-950 border border-gray-800 shadow-xl space-y-4">
                  <div className="flex items-center gap-2 pb-3 border-b border-gray-800">
                    <CheckCircle2 className="w-4 h-4 text-emerald-400" />
                    <h4 className="font-bold text-sm text-white">Dinamik OpenUI Formu</h4>
                  </div>
                  <pre className="text-[11px] font-mono text-indigo-300 bg-gray-900 p-4 rounded-xl overflow-x-auto">
                    {artifact.content}
                  </pre>
                </div>
              </div>
            )}
          </div>
        ) : (
          /* Code Tab */
          <div className="w-full h-full overflow-auto p-4 bg-gray-950 text-slate-200 font-mono text-xs leading-relaxed">
            <pre className="whitespace-pre-wrap">{artifact.content}</pre>
          </div>
        )}
      </div>
    </aside>
  );
}
