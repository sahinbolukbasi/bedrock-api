import { NextResponse } from "next/server";

export async function GET(req: Request) {
  try {
    const models = [
      {
        id: "anthropic.claude-3-5-sonnet-20241022-v2:0",
        object: "model",
        created: 1729555200,
        owned_by: "anthropic",
        name: "Claude 3.5 Sonnet v2",
        context_window: 200000,
        pricing: { input: 0.003, output: 0.015 },
        description: "En gelişmiş frontier reasoning, kodlama ve multimodal zeka modeli.",
      },
      {
        id: "amazon.nova-pro-v1:0",
        object: "model",
        created: 1733184000,
        owned_by: "amazon",
        name: "Amazon Nova Pro",
        context_window: 300000,
        pricing: { input: 0.0008, output: 0.0032 },
        description: "AWS yerel yüksek performanslı, ultra hızlı ve düşük maliyetli kurumsal model.",
      },
      {
        id: "amazon.nova-lite-v1:0",
        object: "model",
        created: 1733184000,
        owned_by: "amazon",
        name: "Amazon Nova Lite",
        context_window: 300000,
        pricing: { input: 0.00006, output: 0.00024 },
        description: "Yüksek hacimli, gerçek zamanlı hızlı işlem ve müşteri destek görevleri için optimize.",
      },
      {
        id: "meta.llama3-3-70b-instruct-v1:0",
        object: "model",
        created: 1733443200,
        owned_by: "meta",
        name: "Llama 3.3 70B Instruct",
        context_window: 128000,
        pricing: { input: 0.00072, output: 0.00072 },
        description: "Açık kaynak lideri 70B çok dilli ve güçlü mantıksal çıkarım modeli.",
      },
      {
        id: "anthropic.claude-3-5-haiku-20241022-v1:0",
        object: "model",
        created: 1729555200,
        owned_by: "anthropic",
        name: "Claude 3.5 Haiku",
        context_window: 200000,
        pricing: { input: 0.001, output: 0.005 },
        description: "Işık hızında tepki süresi ve yüksek doğruluklu kod/metin üretimi.",
      },
    ];

    return NextResponse.json({
      object: "list",
      data: models,
    });
  } catch (err: any) {
    return NextResponse.json({ error: { message: err.message || "Modeller alınamadı." } }, { status: 500 });
  }
}
