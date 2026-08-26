import { NextResponse } from "next/server";

export async function GET(req: Request) {
  try {
    const authHeader = req.headers.get("authorization") || "";
    if (!authHeader) {
      return NextResponse.json({ error: { message: "Unauthorized" } }, { status: 401 });
    }

    return NextResponse.json({
      id: "00000000-0000-0000-0000-000000000001",
      email: "admin@bedrockgateway.com",
      full_name: "Şahin Bölükbaşı",
      role: "admin",
      is_active: true,
      is_verified: true,
      created_at: new Date().toISOString(),
    });
  } catch (err: any) {
    return NextResponse.json({ error: { message: err.message || "Unauthorized" } }, { status: 401 });
  }
}
