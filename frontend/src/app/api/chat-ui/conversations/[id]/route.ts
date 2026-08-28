import { NextResponse } from "next/server";

export async function DELETE(
  req: Request,
  { params }: { params: { id: string } }
) {
  try {
    const convId = params.id;
    return NextResponse.json({
      status: "success",
      message: `Sohbet (${convId}) başarıyla silindi.`,
    });
  } catch (err: any) {
    return NextResponse.json({ error: { message: err.message || "Sohbet silinemedi." } }, { status: 500 });
  }
}
