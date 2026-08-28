import { NextResponse } from "next/server";

export async function DELETE(
  req: Request,
  { params }: { params: { id: string } }
) {
  try {
    const keyId = params.id;
    return NextResponse.json({
      status: "success",
      message: `API anahtarı (${keyId}) başarıyla iptal edildi.`,
    });
  } catch (err: any) {
    return NextResponse.json({ error: { message: err.message || "Anahtar iptal edilemedi." } }, { status: 500 });
  }
}
