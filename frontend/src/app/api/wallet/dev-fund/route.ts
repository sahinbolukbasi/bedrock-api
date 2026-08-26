import { NextResponse } from "next/server";

export async function POST(req: Request) {
  try {
    const body = await req.json();
    const amount = parseFloat(body.amount) || 10;
    const newBalance = 100 + amount;

    return NextResponse.json({
      status: "success",
      message: `$${amount} bakiye başarıyla yüklendi.`,
      new_balance: newBalance,
      new_balance_usd: newBalance.toString(),
    });
  } catch (err: any) {
    return NextResponse.json(
      { error: { message: err.message || "Bakiye yüklenemedi." } },
      { status: 500 }
    );
  }
}
