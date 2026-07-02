import { cookies } from "next/headers";
import { NextResponse } from "next/server";

const DEFAULT_BACKEND_URL = "http://127.0.0.1:8000";

export function getBackendUrl(): string {
  return (
    process.env.CSAUTOBOT_BACKEND_URL ||
    process.env.NEXT_PUBLIC_API_URL ||
    DEFAULT_BACKEND_URL
  ).replace(/\/$/, "");
}

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

  return fetch(`${getBackendUrl()}${path}`, {
    cache: "no-store",
    ...init,
    headers,
  });
}

export async function toNextResponse(response: Response): Promise<NextResponse> {
  const body = await response.text();

  const nextResponse = new NextResponse(body, {
    status: response.status,
    headers: {
      "content-type": response.headers.get("content-type") || "application/json",
    },
  });

  if (response.status === 401) {
    nextResponse.cookies.delete("csautobot_token");
  }

  return nextResponse;
}

export function backendUnavailableResponse(error: unknown): NextResponse {
  return NextResponse.json(
    {
      detail:
        error instanceof Error
          ? error.message
          : "Backend API connection failed",
    },
    { status: 502 },
  );
}
