import { NextResponse } from "next/server";

export const dynamic = "force-dynamic";

export async function POST(request: Request) {
  try {
    const bodyText = await request.text();
    const headers = new Headers();
    headers.set("Content-Type", "application/x-www-form-urlencoded");

    // Replace with your backend URL depending on environment
    // In production, FastAPI runs on port 8000. In local, it might be localhost:8000.
    const backendUrl = process.env.NEXT_PUBLIC_API_URL || "http://127.0.0.1:8000";

    const res = await fetch(`${backendUrl}/api/v1/auth/login`, {
      method: "POST",
      headers,
      body: bodyText,
    });

    if (!res.ok) {
      return NextResponse.json({ detail: "로그인에 실패했습니다." }, { status: res.status });
    }

    const data = await res.json();
    const response = NextResponse.json({ ok: true });
    response.cookies.set("auth_token", data.access_token, {
      httpOnly: true,
      secure: process.env.COOKIE_SECURE === "true",
      sameSite: "lax",
      maxAge: 60 * 60 * 8,
      path: "/",
    });
    return response;
  } catch {
    return NextResponse.json({ detail: "서버 오류가 발생했습니다." }, { status: 500 });
  }
}
