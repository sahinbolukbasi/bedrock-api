import { NextResponse } from "next/server";

export async function GET(req: Request) {
  try {
    return NextResponse.json({
      balance_usd: "100.000000",
      currency: "USD",
      auto_topup_enabled: false,
    });
  } catch (err: any) {
    return NextResponse.json(
      { error: { message: err.message || "Cüzdan bilgisi alınamadı." } },
      { status: 500 }
    );
  }
}
