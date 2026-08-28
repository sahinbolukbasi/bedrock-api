import { NextResponse } from "next/server";

const CONVERSATION_MESSAGES_STORE = new Map<string, any[]>();

// Initialize default conversation messages
CONVERSATION_MESSAGES_STORE.set("conv-init-1", [
  {
    id: "msg-init-1",
    role: "user",
    content: "AWS Bedrock AI Gateway platformu hangi foundation modellerini destekliyor?",
    created_at: new Date(Date.now() - 3600000 * 2).toISOString(),
    tokens: 18,
    cost_usd: 0.000054,
  },
  {
    id: "msg-init-2",
    role: "assistant",
    content: "AWS Bedrock AI Gateway platformu; **Anthropic Claude 3.5 Sonnet & Haiku**, **Amazon Nova Pro, Lite & Micro**, **Meta Llama 3.3 70B & 8B**, **Mistral Large** ve **Amazon Titan Image Generator** dahil en son teknoloji frontier modellerini tek bir OpenAI uyumlu API standardı altında sunmaktadır.",
    created_at: new Date(Date.now() - 3600000 * 2 + 1000).toISOString(),
    tokens: 85,
    cost_usd: 0.001275,
  },
]);

export async function GET(
  req: Request,
  { params }: { params: { id: string } }
) {
  try {
    const convId = params.id;
    const messages = CONVERSATION_MESSAGES_STORE.get(convId) || [];
    return NextResponse.json(messages);
  } catch (err: any) {
    return NextResponse.json({ error: { message: err.message || "Mesajlar yüklenemedi." } }, { status: 500 });
  }
}

export async function POST(
  req: Request,
  { params }: { params: { id: string } }
) {
  try {
    const convId = params.id;
    const body = await req.json();

    const newMsg = {
      id: `msg-${Date.now()}-${Math.random().toString(36).substr(2, 4)}`,
      role: body.role || "user",
      content: body.content || "",
      created_at: new Date().toISOString(),
      tokens: body.tokens || Math.ceil((body.content || "").length / 4),
      cost_usd: body.cost_usd || 0.0001,
    };

    const currentList = CONVERSATION_MESSAGES_STORE.get(convId) || [];
    currentList.push(newMsg);
    CONVERSATION_MESSAGES_STORE.set(convId, currentList);

    return NextResponse.json(newMsg);
  } catch (err: any) {
    return NextResponse.json({ error: { message: err.message || "Mesaj kaydedilemedi." } }, { status: 500 });
  }
}
