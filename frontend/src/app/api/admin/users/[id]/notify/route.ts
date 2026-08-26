import { NextResponse } from "next/server";

export async function POST(
  req: Request,
  { params }: { params: { id: string } }
) {
  try {
    const userId = params.id;
    const body = await req.json();
    const title = body.title || "Sistem Bildirimi";
    const message = body.message || "";
    const channel = body.channel || "EMAIL";

    return NextResponse.json({
      status: "success",
      success: true,
      message: `Kullanıcıya (${userId}) bildirim (${channel}) başarıyla iletildi.`,
      user_id: userId,
      title: title,
      delivered_at: new Date().toISOString(),
    });
  } catch (err: any) {
    return NextResponse.json(
      { error: { message: err.message || "Bildirim iletilemedi." } },
      { status: 500 }
    );
  }
}
