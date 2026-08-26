"use client";

import React, { useState } from "react";
import { BookOpen, Copy, Check, Terminal, Code2 } from "lucide-react";

export default function DocsPage() {
  const [activeTab, setActiveTab] = useState<"python" | "nodejs" | "curl" | "csharp">("python");
  const [copied, setCopied] = useState(false);

  const codeSnippets = {
    python: `import os
from openai import OpenAI

# 1. Initialize OpenAI client pointing to AWS Bedrock Gateway
client = OpenAI(
    base_url="https://api.bedrockgateway.com/v1",
    api_key=os.environ.get("BEDROCK_GATEWAY_API_KEY", "sk-live-a1b2c3d4...")
)

# 2. Execute streaming chat completion with Claude 3.5 Sonnet
response = client.chat.completions.create(
    model="anthropic.claude-3-5-sonnet-20241022-v2:0",
    messages=[
        {"role": "system", "content": "You are a helpful software architect."},
        {"role": "user", "content": "Explain AWS Bedrock inference architecture."}
    ],
    temperature=0.7,
    stream=True
)

for chunk in response:
    if chunk.choices[0].delta.content:
        print(chunk.choices[0].delta.content, end="", flush=True)
`,
    nodejs: `import OpenAI from "openai";

const openai = new OpenAI({
  baseURL: "https://api.bedrockgateway.com/v1",
  apiKey: process.env.BEDROCK_GATEWAY_API_KEY || "sk-live-a1b2c3d4...",
});

async function main() {
  const stream = await openai.chat.completions.create({
    model: "anthropic.claude-3-5-sonnet-20241022-v2:0",
    messages: [{ role: "user", content: "Write a high-concurrency Node.js worker." }],
    stream: true,
  });

  for await (const chunk of stream) {
    process.stdout.write(chunk.choices[0]?.delta?.content || "");
  }
}

main();
`,
    curl: `curl https://api.bedrockgateway.com/v1/chat/completions \\
  -H "Content-Type: application/json" \\
  -H "Authorization: Bearer sk-live-a1b2c3d4..." \\
  -d '{
    "model": "anthropic.claude-3-5-sonnet-20241022-v2:0",
    "messages": [
      {"role": "user", "content": "Hello Bedrock Gateway!"}
    ],
    "stream": false
  }'
`,
    csharp: `using System;
using System.Net.Http;
using System.Net.Http.Json;
using System.Threading.Tasks;

class Program
{
    static async Task Main()
    {
        var client = new HttpClient { BaseAddress = new Uri("https://api.bedrockgateway.com/v1/") };
        client.DefaultRequestHeaders.Add("Authorization", "Bearer sk-live-a1b2c3d4...");

        var requestPayload = new
        {
            model = "anthropic.claude-3-5-sonnet-20241022-v2:0",
            messages = new[]
            {
                new { role = "user", content = "Explain Clean Architecture in .NET" }
            },
            stream = false
        };

        var response = await client.PostAsJsonAsync("chat/completions", requestPayload);
        var result = await response.Content.ReadAsStringAsync();
        Console.WriteLine(result);
    }
}
`
  };

  const handleCopy = (code: string) => {
    navigator.clipboard.writeText(code);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div className="max-w-5xl mx-auto px-4 py-8">
      <div className="border-b border-gray-800 pb-6 mb-8">
        <h1 className="text-2xl font-bold text-white flex items-center gap-2">
          <BookOpen className="w-6 h-6 text-indigo-400" /> Developer API Reference
        </h1>
        <p className="text-gray-400 text-sm mt-1">
          Our API conforms to the OpenAI Chat Completions & Models specification. Existing SDKs work out of the box.
        </p>
      </div>

      {/* Code Snippet Tabs */}
      <div className="rounded-2xl border border-gray-800 bg-gray-900/60 overflow-hidden shadow-2xl mb-10">
        <div className="flex items-center justify-between bg-gray-950 px-4 border-b border-gray-800">
          <div className="flex space-x-1">
            {(["python", "nodejs", "curl", "csharp"] as const).map((tab) => (
              <button
                key={tab}
                onClick={() => setActiveTab(tab)}
                className={`px-4 py-3 text-xs font-semibold uppercase tracking-wider transition border-b-2 ${
                  activeTab === tab
                    ? "border-indigo-500 text-indigo-400"
                    : "border-transparent text-gray-400 hover:text-gray-200"
                }`}
              >
                {tab}
              </button>
            ))}
          </div>

          <button
            onClick={() => handleCopy(codeSnippets[activeTab])}
            className="flex items-center gap-1.5 text-xs text-gray-400 hover:text-white transition"
          >
            {copied ? <Check className="w-4 h-4 text-emerald-400" /> : <Copy className="w-4 h-4" />}
            <span>{copied ? "Copied!" : "Copy Snippet"}</span>
          </button>
        </div>

        <div className="p-6 font-mono text-xs text-gray-300 overflow-x-auto bg-gray-950/70">
          <pre>{codeSnippets[activeTab]}</pre>
        </div>
      </div>

      {/* Endpoint Table */}
      <h2 className="text-lg font-bold text-white mb-4">Core Gateway Endpoints</h2>
      <div className="rounded-2xl border border-gray-800 bg-gray-900/50 overflow-hidden shadow-xl">
        <table className="w-full text-left text-xs text-gray-300">
          <thead className="bg-gray-950/80 border-b border-gray-800 text-gray-400 font-semibold uppercase tracking-wider text-[10px]">
            <tr>
              <th className="px-6 py-4">Method</th>
              <th className="px-6 py-4">Endpoint</th>
              <th className="px-6 py-4">Description</th>
              <th className="px-6 py-4">Auth</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-800/60 font-mono">
            <tr>
              <td className="px-6 py-4 text-indigo-400 font-bold">POST</td>
              <td className="px-6 py-4 text-white">/v1/chat/completions</td>
              <td className="px-6 py-4 font-sans text-gray-400">OpenAI-compatible chat completion (streaming & non-streaming)</td>
              <td className="px-6 py-4 text-amber-400">Bearer sk-...</td>
            </tr>
            <tr>
              <td className="px-6 py-4 text-emerald-400 font-bold">GET</td>
              <td className="px-6 py-4 text-white">/v1/models</td>
              <td className="px-6 py-4 font-sans text-gray-400">List all enabled Bedrock models and token pricing</td>
              <td className="px-6 py-4 text-gray-500">Public</td>
            </tr>
            <tr>
              <td className="px-6 py-4 text-indigo-400 font-bold">POST</td>
              <td className="px-6 py-4 text-white">/v1/images/generations</td>
              <td className="px-6 py-4 font-sans text-gray-400">Titan Image Generator image generation</td>
              <td className="px-6 py-4 text-amber-400">Bearer sk-...</td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
  );
}
