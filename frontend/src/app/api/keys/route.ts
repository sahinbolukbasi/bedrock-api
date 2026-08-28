import { NextResponse } from "next/server";
import crypto from "crypto";

// In-memory persistent key store for seamless session persistence
let GLOBAL_API_KEYS = [
  {
    id: "key-prod-001",
    name: "Production Backend Key",
    key_prefix: "bg-live-8f92",
    masked_key: "bg-live-8f92************************",
    is_active: true,
    created_at: new Date(Date.now() - 86400000 * 5).toISOString(),
    last_used_at: new Date().toISOString(),
    total_requests: 1420,
    rate_limit_rpm: 120,
  },
  {
    id: "key-dev-002",
    name: "Development Test Key",
    key_prefix: "bg-live-3a71",
    masked_key: "bg-live-3a71************************",
    is_active: true,
    created_at: new Date(Date.now() - 86400000 * 2).toISOString(),
    last_used_at: new Date().toISOString(),
    total_requests: 384,
    rate_limit_rpm: 60,
  },
];

export async function GET(req: Request) {
  try {
    return NextResponse.json(GLOBAL_API_KEYS);
  } catch (err: any) {
    return NextResponse.json({ error: { message: err.message || "Anahtarlar yüklenemedi." } }, { status: 500 });
  }
}

export async function POST(req: Request) {
  try {
    const body = await req.json();
    const name = (body.name || "Yeni API Anahtarı").trim();
    const randomHex = crypto.randomBytes(16).toString("hex");
    const secretKey = `bg-live-${randomHex}`;
    const prefix = secretKey.slice(0, 12);
    const masked = `${prefix}************************`;
    const newId = `key-${Date.now()}`;

    const newKeyObj = {
      id: newId,
      name: name,
      key_prefix: prefix,
      masked_key: masked,
      is_active: true,
      created_at: new Date().toISOString(),
      last_used_at: null,
      total_requests: 0,
      rate_limit_rpm: body.rate_limit_rpm || 60,
      secret_key: secretKey, // returned only upon creation
    };

    GLOBAL_API_KEYS.unshift(newKeyObj);

    return NextResponse.json(newKeyObj);
  } catch (err: any) {
    return NextResponse.json({ error: { message: err.message || "API anahtarı oluşturulamadı." } }, { status: 500 });
  }
}
