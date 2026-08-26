import { NextResponse } from "next/server";

export async function POST(
  req: Request,
  { params }: { params: { id: string } }
) {
  try {
    const userId = params.id;
    let newBalance = 100;

    const url = new URL(req.url);
    const queryBalance = url.searchParams.get("new_balance_usd");
    if (queryBalance) {
      newBalance = parseFloat(queryBalance);
    } else {
      try {
        const body = await req.json();
        if (body.new_balance_usd !== undefined) {
          newBalance = parseFloat(body.new_balance_usd);
        } else if (body.amount !== undefined) {
          newBalance = parseFloat(body.amount);
        }
      } catch {
        // body parsing optional if query param exists
      }
    }

    return NextResponse.json({
      status: "success",
      message: `Kullanıcı (ID: ${userId}) bakiyesi başarıyla $${newBalance.toFixed(2)} olarak güncellendi.`,
      user_id: userId,
      new_balance_usd: newBalance,
    });
  } catch (err: any) {
    return NextResponse.json(
      { error: { message: err.message || "Bakiye güncellenemedi." } },
      { status: 500 }
    );
  }
}
