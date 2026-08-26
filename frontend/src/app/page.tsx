"use client";

import React, { useState, useEffect } from "react";
import Link from "next/link";
import { 
  Zap, 
  ShieldCheck, 
  Coins, 
  Code2, 
  Layers, 
  ArrowRight, 
  CheckCircle2, 
  Lock, 
  Sparkles,
  Server,
  Terminal,
  Cpu,
  UserPlus,
  LogIn,
  Key
} from "lucide-react";
import { getAuthToken } from "../lib/api";

export default function LandingPage() {
  const [isLoggedIn, setIsLoggedIn] = useState<boolean>(false);
  const [activeTab, setActiveTab] = useState<"python" | "node" | "curl">("python");

  useEffect(() => {
    setIsLoggedIn(!!getAuthToken());
  }, []);

  return (
    <div className="relative overflow-hidden">
      {/* Dynamic Background Glows */}
      <div className="absolute top-1/6 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[700px] h-[400px] bg-gradient-to-r from-indigo-500/20 via-purple-500/20 to-amber-500/20 blur-[140px] pointer-events-none" />
      <div className="absolute top-2/3 right-10 w-[400px] h-[400px] bg-indigo-600/10 blur-[150px] pointer-events-none" />

      {/* Hero Section */}
      <section className="max-w-6xl mx-auto px-4 pt-16 sm:pt-24 pb-16 text-center relative z-10">
        <div className="inline-flex items-center gap-2 px-3.5 py-1.5 rounded-full border border-indigo-500/30 bg-indigo-950/40 text-indigo-300 text-xs font-medium mb-8 backdrop-blur-md">
          <Sparkles className="w-3.5 h-3.5 text-amber-400 animate-pulse" />
          <span>Unified OpenAI-Compatible Gateway for AWS Bedrock Frontier AI</span>
        </div>

        <h1 className="text-4xl sm:text-6xl lg:text-7xl font-extrabold text-white tracking-tight max-w-5xl mx-auto leading-[1.15]">
          Supercharge your Apps with{" "}
          <span className="bg-gradient-to-r from-indigo-400 via-purple-400 to-amber-400 bg-clip-text text-transparent">
            AWS Bedrock
          </span>{" "}
          via One Single API Key
        </h1>

        <p className="mt-6 text-base sm:text-xl text-gray-400 max-w-3xl mx-auto leading-relaxed">
          Access frontier AI models including <strong className="text-gray-200">Claude 3.5 Sonnet v2</strong>, <strong className="text-gray-200">Amazon Nova Pro</strong>, and <strong className="text-gray-200">Meta Llama 3.3 70B</strong> with standard OpenAI SDKs. Zero AWS account or IAM credentials needed.
        </p>

        {/* CTA Buttons */}
        <div className="mt-10 flex flex-wrap items-center justify-center gap-4">
          {isLoggedIn ? (
            <Link
              href="/chat"
              className="flex items-center gap-2 px-8 py-3.5 rounded-xl bg-indigo-600 hover:bg-indigo-500 text-white font-bold text-sm transition shadow-lg shadow-indigo-600/30 transform hover:-translate-y-0.5"
            >
              Open Console & Chat <ArrowRight className="w-4 h-4" />
            </Link>
          ) : (
            <>
              <Link
                href="/register"
                className="flex items-center gap-2 px-8 py-3.5 rounded-xl bg-gradient-to-r from-indigo-600 to-purple-600 hover:from-indigo-500 hover:to-purple-500 text-white font-bold text-sm transition shadow-lg shadow-indigo-600/30 transform hover:-translate-y-0.5"
              >
                <UserPlus className="w-4 h-4" /> Get Started Free
              </Link>
              <Link
                href="/login"
                className="flex items-center gap-2 px-7 py-3.5 rounded-xl bg-gray-900/90 hover:bg-gray-800 border border-gray-800 text-gray-200 font-semibold text-sm transition"
              >
                <LogIn className="w-4 h-4 text-indigo-400" /> Sign In to Account
              </Link>
            </>
          )}
          <Link
            href="/models"
            className="flex items-center gap-2 px-6 py-3.5 rounded-xl bg-gray-900/40 hover:bg-gray-800/60 border border-gray-800/80 text-gray-400 hover:text-gray-200 font-medium text-sm transition"
          >
            <Cpu className="w-4 h-4 text-amber-400" /> Explore Models
          </Link>
        </div>

        {/* Interactive Code Snippet Tabs */}
        <div className="mt-14 max-w-3xl mx-auto rounded-2xl border border-gray-800 bg-gray-950/90 shadow-2xl p-6 text-left font-mono text-xs text-gray-300 backdrop-blur-md">
          <div className="flex items-center justify-between border-b border-gray-800 pb-3 mb-4">
            <div className="flex items-center gap-2">
              <div className="w-3 h-3 rounded-full bg-red-500/80" />
              <div className="w-3 h-3 rounded-full bg-yellow-500/80" />
              <div className="w-3 h-3 rounded-full bg-green-500/80" />
              <div className="flex gap-2 ml-4">
                <button
                  onClick={() => setActiveTab("python")}
                  className={`px-2.5 py-1 rounded text-[11px] font-sans font-medium transition ${
                    activeTab === "python" ? "bg-indigo-600 text-white" : "text-gray-400 hover:text-gray-200"
                  }`}
                >
                  Python
                </button>
                <button
                  onClick={() => setActiveTab("node")}
                  className={`px-2.5 py-1 rounded text-[11px] font-sans font-medium transition ${
                    activeTab === "node" ? "bg-indigo-600 text-white" : "text-gray-400 hover:text-gray-200"
                  }`}
                >
                  Node.js
                </button>
                <button
                  onClick={() => setActiveTab("curl")}
                  className={`px-2.5 py-1 rounded text-[11px] font-sans font-medium transition ${
                    activeTab === "curl" ? "bg-indigo-600 text-white" : "text-gray-400 hover:text-gray-200"
                  }`}
                >
                  cURL
                </button>
              </div>
            </div>
            <span className="text-[11px] text-emerald-400 font-sans hidden sm:inline">✓ 100% OpenAI Drop-In</span>
          </div>

          {activeTab === "python" && (
            <pre className="overflow-x-auto text-gray-300 leading-relaxed">
              <span className="text-purple-400">from</span> openai <span className="text-purple-400">import</span> OpenAI<br/><br/>
              client = OpenAI(<br/>
              &nbsp;&nbsp;base_url=<span className="text-emerald-300">"http://bedrock-gateway-alb-664380835.us-east-1.elb.amazonaws.com:8000/v1"</span>,<br/>
              &nbsp;&nbsp;api_key=<span className="text-amber-300">"sk-live-your-gateway-key"</span><br/>
              )<br/><br/>
              response = client.chat.completions.create(<br/>
              &nbsp;&nbsp;model=<span className="text-emerald-300">"anthropic.claude-3-5-sonnet-20241022-v2:0"</span>,<br/>
              &nbsp;&nbsp;messages=[&#123;<span className="text-amber-300">"role"</span>: <span className="text-amber-300">"user"</span>, <span className="text-amber-300">"content"</span>: <span className="text-amber-300">"Explain quantum computing in 3 sentences."</span>&#125;],<br/>
              &nbsp;&nbsp;stream=<span className="text-indigo-400">True</span><br/>
              )<br/>
              <span className="text-purple-400">for</span> chunk <span className="text-purple-400">in</span> response:<br/>
              &nbsp;&nbsp;print(chunk.choices[0].delta.content <span className="text-purple-400">or</span> <span className="text-emerald-300">""</span>, end=<span className="text-emerald-300">""</span>, flush=<span className="text-indigo-400">True</span>)
            </pre>
          )}

          {activeTab === "node" && (
            <pre className="overflow-x-auto text-gray-300 leading-relaxed">
              <span className="text-purple-400">import</span> OpenAI <span className="text-purple-400">from</span> <span className="text-emerald-300">"openai"</span>;<br/><br/>
              <span className="text-purple-400">const</span> client = <span className="text-purple-400">new</span> OpenAI(&#123;<br/>
              &nbsp;&nbsp;baseURL: <span className="text-emerald-300">"http://bedrock-gateway-alb-664380835.us-east-1.elb.amazonaws.com:8000/v1"</span>,<br/>
              &nbsp;&nbsp;apiKey: <span className="text-amber-300">"sk-live-your-gateway-key"</span>,<br/>
              &#125;);<br/><br/>
              <span className="text-purple-400">const</span> stream = <span className="text-purple-400">await</span> client.chat.completions.create(&#123;<br/>
              &nbsp;&nbsp;model: <span className="text-emerald-300">"anthropic.claude-3-5-sonnet-20241022-v2:0"</span>,<br/>
              &nbsp;&nbsp;messages: [&#123; role: <span className="text-amber-300">"user"</span>, content: <span className="text-amber-300">"Hello AWS Bedrock!"</span> &#125;],<br/>
              &nbsp;&nbsp;stream: <span className="text-indigo-400">true</span>,<br/>
              &#125;);<br/>
              <span className="text-purple-400">for await</span> (<span className="text-purple-400">const</span> chunk <span className="text-purple-400">of</span> stream) &#123;<br/>
              &nbsp;&nbsp;process.stdout.write(chunk.choices[0]?.delta?.content || <span className="text-emerald-300">""</span>);<br/>
              &#125;
            </pre>
          )}

          {activeTab === "curl" && (
            <pre className="overflow-x-auto text-gray-300 leading-relaxed">
              curl -X POST http://bedrock-gateway-alb-664380835.us-east-1.elb.amazonaws.com:8000/v1/chat/completions \<br/>
              &nbsp;&nbsp;-H <span className="text-emerald-300">"Authorization: Bearer sk-live-your-gateway-key"</span> \<br/>
              &nbsp;&nbsp;-H <span className="text-emerald-300">"Content-Type: application/json"</span> \<br/>
              &nbsp;&nbsp;-d '&#123;<br/>
              &nbsp;&nbsp;&nbsp;&nbsp;<span className="text-amber-300">"model"</span>: <span className="text-emerald-300">"anthropic.claude-3-5-sonnet-20241022-v2:0"</span>,<br/>
              &nbsp;&nbsp;&nbsp;&nbsp;<span className="text-amber-300">"messages"</span>: [&#123;<span className="text-amber-300">"role"</span>: <span className="text-amber-300">"user"</span>, <span className="text-amber-300">"content"</span>: <span className="text-amber-300">"Hello Bedrock"</span>&#125;],<br/>
              &nbsp;&nbsp;&nbsp;&nbsp;<span className="text-amber-300">"stream"</span>: <span className="text-indigo-400">true</span><br/>
              &nbsp;&nbsp;&#125;'
            </pre>
          )}
        </div>
      </section>

      {/* How it Works 3 Steps */}
      <section className="max-w-6xl mx-auto px-4 py-16 border-t border-gray-900">
        <div className="text-center mb-12">
          <h2 className="text-2xl sm:text-3xl font-bold text-white">How It Works in 3 Simple Steps</h2>
          <p className="text-gray-400 text-sm mt-2">Start streaming from AWS Bedrock in less than 2 minutes.</p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
          <div className="p-6 rounded-2xl bg-gray-900/40 border border-gray-800 text-center">
            <div className="w-12 h-12 mx-auto rounded-full bg-indigo-950 border border-indigo-800 text-indigo-400 flex items-center justify-center font-bold text-lg mb-4">
              1
            </div>
            <h3 className="text-lg font-semibold text-white">Create Account & Add Credit</h3>
            <p className="text-gray-400 text-sm mt-2">
              Sign up in seconds. Fund your account with pre-paid credits via Stripe. No subscription fees.
            </p>
          </div>

          <div className="p-6 rounded-2xl bg-gray-900/40 border border-gray-800 text-center">
            <div className="w-12 h-12 mx-auto rounded-full bg-purple-950 border border-purple-800 text-purple-400 flex items-center justify-center font-bold text-lg mb-4">
              2
            </div>
            <h3 className="text-lg font-semibold text-white">Generate API Key</h3>
            <p className="text-gray-400 text-sm mt-2">
              Create scoped `sk-live-...` keys with custom spending and rate limits.
            </p>
          </div>

          <div className="p-6 rounded-2xl bg-gray-900/40 border border-gray-800 text-center">
            <div className="w-12 h-12 mx-auto rounded-full bg-amber-950 border border-amber-800 text-amber-400 flex items-center justify-center font-bold text-lg mb-4">
              3
            </div>
            <h3 className="text-lg font-semibold text-white">Plug into any OpenAI SDK</h3>
            <p className="text-gray-400 text-sm mt-2">
              Point your existing code to our gateway URL and enjoy frontier AI models instantly.
            </p>
          </div>
        </div>
      </section>

      {/* Architectural Highlights */}
      <section className="max-w-6xl mx-auto px-4 py-16 border-t border-gray-900">
        <div className="text-center mb-12">
          <h2 className="text-2xl sm:text-3xl font-bold text-white">Enterprise AI Gateway Architecture</h2>
          <p className="text-gray-400 text-sm mt-2">Engineered for security, sub-second latency, and strict transactional consistency.</p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <div className="p-6 rounded-2xl bg-gray-900/50 border border-gray-800 hover:border-indigo-500/50 transition">
            <div className="w-10 h-10 rounded-xl bg-indigo-950 flex items-center justify-center text-indigo-400 mb-4 border border-indigo-800/50">
              <Lock className="w-5 h-5" />
            </div>
            <h3 className="font-semibold text-lg text-white">Zero AWS Key Exposure</h3>
            <p className="text-gray-400 text-sm mt-2">
              Developers never touch AWS IAM keys. Access models via platform-hashed API keys (`sk-live-...`) with granular spending limits.
            </p>
          </div>

          <div className="p-6 rounded-2xl bg-gray-900/50 border border-gray-800 hover:border-purple-500/50 transition">
            <div className="w-10 h-10 rounded-xl bg-purple-950 flex items-center justify-center text-purple-400 mb-4 border border-purple-800/50">
              <Coins className="w-5 h-5" />
            </div>
            <h3 className="font-semibold text-lg text-white">Atomic Credit Ledger</h3>
            <p className="text-gray-400 text-sm mt-2">
              PostgreSQL row-level locking (`SELECT ... FOR UPDATE`) prevents concurrent balance overdrafts during high-frequency parallel inference.
            </p>
          </div>

          <div className="p-6 rounded-2xl bg-gray-900/50 border border-gray-800 hover:border-amber-500/50 transition">
            <div className="w-10 h-10 rounded-xl bg-amber-950 flex items-center justify-center text-amber-400 mb-4 border border-amber-800/50">
              <Zap className="w-5 h-5" />
            </div>
            <h3 className="font-semibold text-lg text-white">Real-Time SSE Streaming</h3>
            <p className="text-gray-400 text-sm mt-2">
              Ultra-low latency token-by-token streaming with immediate cost calculation and graceful client disconnect protection.
            </p>
          </div>
        </div>
      </section>

      {/* Footer CTA */}
      <section className="max-w-4xl mx-auto px-4 py-20 text-center">
        <div className="p-10 rounded-3xl bg-gradient-to-b from-gray-900 to-gray-950 border border-gray-800 shadow-2xl relative overflow-hidden">
          <div className="absolute top-0 right-0 w-64 h-64 bg-indigo-500/10 rounded-full blur-3xl pointer-events-none" />
          <h2 className="text-3xl font-extrabold text-white">Ready to connect to AWS Bedrock?</h2>
          <p className="text-gray-400 text-sm mt-3 max-w-xl mx-auto">
            Create your account today, generate an API key, and start querying Claude 3.5, Nova, and Llama 3 in minutes.
          </p>
          <div className="mt-8 flex justify-center gap-4">
            <Link
              href="/register"
              className="px-8 py-3 rounded-xl bg-indigo-600 hover:bg-indigo-500 text-white font-bold text-sm transition shadow-lg shadow-indigo-600/30"
            >
              Get Started Now
            </Link>
            <Link
              href="/login"
              className="px-6 py-3 rounded-xl bg-gray-800 hover:bg-gray-700 text-gray-200 font-semibold text-sm transition"
            >
              Sign In
            </Link>
          </div>
        </div>
      </section>
    </div>
  );
}
