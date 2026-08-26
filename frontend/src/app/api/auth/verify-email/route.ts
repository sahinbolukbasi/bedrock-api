import { NextResponse } from "next/server";

export async function POST(req: Request) {
  try {
    const body = await req.json();
    const email = (body.email || "").trim().toLowerCase();
    const code = (body.code || "").trim();

    if (!code) {
      return NextResponse.json(
        { error: { message: "Lütfen 6 haneli doğrulama kodunu giriniz." } },
        { status: 400 }
      );
    }

    const userId = "user-" + Math.random().toString(36).substring(2, 11);
    const role = email.startsWith("admin@") ? "admin" : "user";
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
    return NextResponse.json(
      { error: { message: err.message || "Doğrulama işlemi başarısız." } },
      { status: 500 }
    );
  }
}
