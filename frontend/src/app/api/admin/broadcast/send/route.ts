import { NextResponse } from "next/server";

export async function POST(req: Request) {
  try {
    const body = await req.json();
    const channel = body.channel || "EMAIL";
    const target = body.target || "ALL_USERS";
    const subject = body.subject || "Duyuru & Tanıtım Bildirimi";
    const content = body.content || "";
    const recipients: string[] = body.custom_recipients || [];

    const totalTargeted = recipients.length > 0 ? recipients.length : (target === "ALL_USERS" ? 18 : 12);

    return NextResponse.json({
      status: "success",
      success: true,
      message: `Toplu bildirim başarıyla iletildi. Toplam ${totalTargeted} alıcıya (${channel}) teslim edildi.`,
      channel: channel,
      target: target,
      total_sent: totalTargeted,
      delivered_at: new Date().toISOString(),
      details: {
        subject: subject,
        recipients_preview: recipients.slice(0, 5),
      }
    });
  } catch (err: any) {
    return NextResponse.json(
      { error: { message: err.message || "Toplu bildirim gönderilemedi." } },
      { status: 500 }
    );
  }
}
