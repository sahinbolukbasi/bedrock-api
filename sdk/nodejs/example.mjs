/**
 * AWS Bedrock AI Gateway - Node.js Quickstart
 * Using standard OpenAI official Node.js SDK
 */

import OpenAI from "openai";

const client = new OpenAI({
  baseURL: process.env.BEDROCK_GATEWAY_URL || "http://localhost:8000/v1",
  apiKey: process.env.BEDROCK_API_KEY || "sk-live-sample-key-123",
});

async function main() {
  console.log("Streaming response from Bedrock (Amazon Nova Pro)...");

  const stream = await client.chat.completions.create({
    model: "amazon.nova-pro-v1:0",
    messages: [
      { role: "system", content: "You are an expert DevOps engineer." },
      { role: "user", content: "Write a high-performance Terraform module for AWS ECS Fargate." }
    ],
    stream: true,
  });

  for await (const chunk of stream) {
    process.stdout.write(chunk.choices[0]?.delta?.content || "");
  }
  console.log("\n");
}

main().catch(console.error);
