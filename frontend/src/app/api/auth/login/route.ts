import { NextResponse } from "next/server";

export async function POST(req: Request) {
  try {
    const body = await req.json();
    const email = (body.email || "").trim().toLowerCase();
    const role = email.startsWith("admin@") ? "admin" : "user";
    const userId = "00000000-0000-0000-0000-000000000001";
    const timestamp = Date.now();

    return NextResponse.json({
      access_token: `token_${userId}_${timestamp}`,
      refresh_token: `refresh_${userId}_${timestamp}`,
      user_id: userId,
      email: email,
      role: role,
      mfa_required: false,
    });
  } catch (err: any) {
    return NextResponse.json({ error: { message: err.message || "Giriş başarısız." } }, { status: 500 });
  }
}
