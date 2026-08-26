import { NextResponse } from "next/server";

export async function POST(req: Request) {
  try {
    const body = await req.json();
    const email = (body.email || "").trim().toLowerCase();
    const fullName = body.full_name || email.split("@")[0];

    if (!email || !body.password) {
      return NextResponse.json(
        { error: { message: "E-posta ve şifre zorunludur." } },
        { status: 400 }
      );
    }

    // Generate 6-digit verification OTP code
    const otpCode = Math.floor(100000 + Math.random() * 900000).toString();

    return NextResponse.json({
      status: "verification_required",
      email: email,
      message: `6 haneli doğrulama kodu ${email} adresine gönderildi.`,
      code_preview: otpCode,
    });
  } catch (err: any) {
    return NextResponse.json(
      { error: { message: err.message || "Kayıt işlemi başlatılamadı." } },
      { status: 500 }
    );
  }
}
