import { NextResponse } from "next/server";

const BACKEND_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

/**
 * Proxy: Forwards all chat/completions requests directly to the
 * FastAPI backend which calls real AWS Bedrock models and charges the wallet.
 */
export async function POST(req: Request) {
  try {
    const authHeader = req.headers.get("authorization") || "";
    const body = await req.text(); // forward raw body as-is
    const isStream = (() => {
      try {
        return JSON.parse(body)?.stream === true;
      } catch {
        return false;
      }
    })();

    const backendRes = await fetch(`${BACKEND_URL}/v1/chat/completions`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Authorization: authHeader,
      },
      body,
      // @ts-ignore — needed for Node.js fetch to stream
      duplex: "half",
    });

    if (!backendRes.ok) {
      let errText = "";
      try {
        errText = await backendRes.text();
      } catch {}
      let errJson: any = {};
      try {
        errJson = JSON.parse(errText);
      } catch {
        errJson = { error: { message: errText || "Backend error" } };
      }
      return NextResponse.json(errJson, { status: backendRes.status });
    }

    // For streaming responses, pipe the SSE stream directly to the client
    if (isStream && backendRes.body) {
      return new Response(backendRes.body, {
        status: 200,
        headers: {
          "Content-Type": "text/event-stream",
          "Cache-Control": "no-cache",
          Connection: "keep-alive",
          "X-Accel-Buffering": "no",
        },
      });
    }

    // Non-streaming — return JSON
    const data = await backendRes.json();
    return NextResponse.json(data);
  } catch (err: any) {
    console.error("[/v1/chat/completions proxy error]", err);
    return NextResponse.json(
      { error: { message: err?.message || "AI gateway unreachable", type: "proxy_error" } },
      { status: 503 }
    );
  }
}
