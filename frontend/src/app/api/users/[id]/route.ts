import {
  backendUnavailableResponse,
  proxyBackend,
  toNextResponse,
} from "@/lib/backend";
import { NextResponse } from "next/server";

export const dynamic = "force-dynamic";

function getUserId(request: Request): string | null {
  return new URL(request.url).pathname.split("/").filter(Boolean).pop() || null;
}

export async function PUT(request: Request) {
  try {
    const id = getUserId(request);
    if (!id) {
      return NextResponse.json({ detail: "User id is required" }, { status: 400 });
    }

    const body = await request.text();
    const res = await proxyBackend(`/api/v1/users/${id}`, {
      method: "PUT",
      headers: { "Content-Type": "application/json" },
      body,
    });
    return await toNextResponse(res);
  } catch (error) {
    return backendUnavailableResponse(error);
  }
}

export async function DELETE(request: Request) {
  try {
    const id = getUserId(request);
    if (!id) {
      return NextResponse.json({ detail: "User id is required" }, { status: 400 });
    }

    const res = await proxyBackend(`/api/v1/users/${id}`, { method: "DELETE" });
    if (res.status === 204) {
      return new NextResponse(null, { status: 204 });
    }

    return await toNextResponse(res);
  } catch (error) {
    return backendUnavailableResponse(error);
  }
}
