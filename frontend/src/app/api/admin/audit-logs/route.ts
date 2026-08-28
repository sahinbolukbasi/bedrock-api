import { NextResponse } from "next/server";

export async function GET(req: Request) {
  try {
    const logs = [
      {
        id: "log-001",
        timestamp: new Date(Date.now() - 1000 * 60 * 2).toISOString(),
        action: "MODEL_INFERENCE",
        user_email: "sahinbolukbasii@gmail.com",
        model_id: "anthropic.claude-3-5-sonnet-20241022-v2:0",
        tokens_in: 45,
        tokens_out: 120,
        cost_usd: 0.00225,
        status: "200_OK",
        ip_address: "127.0.0.1",
      },
      {
        id: "log-002",
        timestamp: new Date(Date.now() - 1000 * 60 * 12).toISOString(),
        action: "API_KEY_CREATED",
        user_email: "admin@bedrockgateway.com",
        model_id: "-",
        tokens_in: 0,
        tokens_out: 0,
        cost_usd: 0.0,
        status: "200_OK",
        ip_address: "127.0.0.1",
      },
      {
        id: "log-003",
        timestamp: new Date(Date.now() - 1000 * 60 * 35).toISOString(),
        action: "WALLET_TOPUP",
        user_email: "sahinbolukbasii@gmail.com",
        model_id: "-",
        tokens_in: 0,
        tokens_out: 0,
        cost_usd: 0.0,
        status: "SUCCESS_+$10.00",
        ip_address: "127.0.0.1",
      },
      {
        id: "log-004",
        timestamp: new Date(Date.now() - 1000 * 60 * 60).toISOString(),
        action: "BROADCAST_CAMPAIGN",
        user_email: "admin@bedrockgateway.com",
        model_id: "-",
        tokens_in: 0,
        tokens_out: 0,
        cost_usd: 0.0,
        status: "SENT_TO_ALL",
        ip_address: "127.0.0.1",
      },
    ];

    return NextResponse.json(logs);
  } catch (err: any) {
    return NextResponse.json({ error: { message: err.message || "Loglar yüklenemedi." } }, { status: 500 });
  }
}
