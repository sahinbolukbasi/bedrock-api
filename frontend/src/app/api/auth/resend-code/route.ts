import { NextResponse } from "next/server";

export async function POST(req: Request) {
  try {
    const body = await req.json();
    const email = (body.email || "").trim().toLowerCase();
    const otpCode = Math.floor(100000 + Math.random() * 900000).toString();

    return NextResponse.json({
      status: "code_resent",
      email: email,
      message: "Yeni 6 haneli doğrulama kodu başarıyla iletildi.",
      code_preview: otpCode,
    });
  } catch (err: any) {
    return NextResponse.json(
      { error: { message: err.message || "Kod gönderilemedi." } },
      { status: 500 }
    );
  }
}
