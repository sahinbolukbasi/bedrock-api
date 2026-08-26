import React from "react";
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
  Server
} from "lucide-react";

export default function LandingPage() {
  return (
    <div className="relative overflow-hidden">
      {/* Background Glows */}
      <div className="absolute top-1/4 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[600px] h-[350px] bg-gradient-to-r from-indigo-500/20 via-purple-500/20 to-amber-500/20 blur-[120px] pointer-events-none" />

      {/* Hero Section */}
      <section className="max-w-6xl mx-auto px-4 pt-20 pb-16 text-center relative z-10">
        <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full border border-indigo-500/30 bg-indigo-950/40 text-indigo-300 text-xs font-medium mb-6">
          <Sparkles className="w-3.5 h-3.5 text-amber-400" />
          <span>Unified Access to Anthropic Claude 3.5, Amazon Nova & Meta Llama 3</span>
        </div>

        <h1 className="text-4xl sm:text-6xl font-extrabold text-white tracking-tight max-w-4xl mx-auto leading-tight">
          The <span className="bg-gradient-to-r from-indigo-400 via-purple-400 to-amber-400 bg-clip-text text-transparent">AWS Bedrock AI Gateway</span> for Developers
        </h1>

        <p className="mt-6 text-lg sm:text-xl text-gray-400 max-w-2xl mx-auto">
          Access frontier AI models on AWS Bedrock using standard OpenAI SDKs and API keys. 
          Zero AWS credentials required. Pay-as-you-go with transparent token-level metering.
        </p>

        <div className="mt-10 flex flex-wrap items-center justify-center gap-4">
          <Link
            href="/chat"
            className="flex items-center gap-2 px-6 py-3 rounded-xl bg-indigo-600 hover:bg-indigo-500 text-white font-semibold text-sm transition shadow-lg shadow-indigo-600/30"
          >
            Launch Chat Playground <ArrowRight className="w-4 h-4" />
          </Link>
          <Link
            href="/docs"
            className="flex items-center gap-2 px-6 py-3 rounded-xl bg-gray-900 hover:bg-gray-800 border border-gray-800 text-gray-300 font-semibold text-sm transition"
          >
            <Code2 className="w-4 h-4 text-indigo-400" /> View API Docs
          </Link>
        </div>

        {/* Code Snippet Card */}
        <div className="mt-14 max-w-3xl mx-auto rounded-2xl border border-gray-800 bg-gray-950/80 shadow-2xl p-6 text-left font-mono text-xs text-gray-300 backdrop-blur-md">
          <div className="flex items-center justify-between border-b border-gray-800 pb-3 mb-4">
            <div className="flex items-center gap-2">
              <div className="w-3 h-3 rounded-full bg-red-500/80" />
              <div className="w-3 h-3 rounded-full bg-yellow-500/80" />
              <div className="w-3 h-3 rounded-full bg-green-500/80" />
              <span className="text-gray-500 text-[11px] ml-2">openai_drop_in_example.py</span>
            </div>
            <span className="text-[11px] text-emerald-400">100% OpenAI SDK Compatible</span>
          </div>
          <pre className="overflow-x-auto text-gray-300">
            <span className="text-purple-400">from</span> openai <span className="text-purple-400">import</span> OpenAI<br/><br/>
            client = OpenAI(<br/>
            &nbsp;&nbsp;base_url=<span className="text-emerald-300">"https://api.bedrockgateway.com/v1"</span>,<br/>
            &nbsp;&nbsp;api_key=<span className="text-amber-300">"sk-live-a1b2c3d4..."</span><br/>
            )<br/><br/>
            response = client.chat.completions.create(<br/>
            &nbsp;&nbsp;model=<span className="text-emerald-300">"anthropic.claude-3-5-sonnet-20241022-v2:0"</span>,<br/>
            &nbsp;&nbsp;messages=[&#123;<span className="text-amber-300">"role"</span>: <span className="text-amber-300">"user"</span>, <span className="text-amber-300">"content"</span>: <span className="text-amber-300">"Architect a resilient multi-tenant SaaS"</span>&#125;],<br/>
            &nbsp;&nbsp;stream=<span className="text-indigo-400">True</span><br/>
            )
          </pre>
        </div>
      </section>

      {/* Core Architectural Pillars */}
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
    </div>
  );
}
