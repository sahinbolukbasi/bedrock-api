import { NextResponse } from "next/server";

let GLOBAL_CONVERSATIONS = [
  {
    id: "conv-init-1",
    title: "🚀 AWS Bedrock Gateway Başlangıç & Mimari Danışmanlığı",
    model_id: "anthropic.claude-3-5-sonnet-20241022-v2:0",
    system_prompt: "You are an expert AI assistant powered by Amazon Bedrock.",
    temperature: 0.7,
    created_at: new Date(Date.now() - 3600000 * 2).toISOString(),
    message_count: 2,
  },
];

export async function GET(req: Request) {
  try {
    return NextResponse.json(GLOBAL_CONVERSATIONS);
  } catch (err: any) {
    return NextResponse.json({ error: { message: err.message || "Sohbetler yüklenemedi." } }, { status: 500 });
  }
}

export async function POST(req: Request) {
  try {
    const body = await req.json();
    const newConv = {
      id: `conv-${Date.now()}`,
      title: body.title || "Yeni Sohbet",
      model_id: body.model_id || "anthropic.claude-3-5-sonnet-20241022-v2:0",
      system_prompt: body.system_prompt || "You are an expert AI assistant powered by Amazon Bedrock.",
      temperature: body.temperature || 0.7,
      created_at: new Date().toISOString(),
      message_count: 0,
    };

    GLOBAL_CONVERSATIONS.unshift(newConv);
    return NextResponse.json(newConv);
  } catch (err: any) {
    return NextResponse.json({ error: { message: err.message || "Sohbet oluşturulamadı." } }, { status: 500 });
  }
}
