import { cookies } from "next/headers";
import { NextResponse } from "next/server";

const BACKEND_URL =
  process.env.CSAUTOBOT_BACKEND_URL ||
  process.env.NEXT_PUBLIC_API_URL ||
  "http://127.0.0.1:8000";

export async function proxyBackend(
  path: string,
  init: RequestInit = {},
): Promise<Response> {
  const cookieStore = await cookies();
  const token = cookieStore.get("csautobot_token")?.value;

  const headers = new Headers(init.headers);
  if (token) {
    headers.set("Authorization", `Bearer ${token}`);
  }

  return fetch(`${BACKEND_URL}${path}`, {
    ...init,
    headers,
    cache: "no-store",
  });
}

export async function toNextResponse(res: Response): Promise<NextResponse> {
  const contentType = res.headers.get("Content-Type") || "application/json";
  const body = await res.text();
  return new NextResponse(body, {
    status: res.status,
    headers: { "Content-Type": contentType },
  });
}

export function backendUnavailableResponse(error: unknown): NextResponse {
  const message =
    error instanceof Error ? error.message : "Backend unavailable";
  return NextResponse.json(
    { detail: `백엔드 서버에 연결할 수 없습니다: ${message}` },
    { status: 503 },
  );
}
