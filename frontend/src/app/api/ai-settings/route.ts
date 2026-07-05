import {
  backendUnavailableResponse,
  proxyBackend,
  toNextResponse,
} from "@/lib/backend";
import type { NextRequest } from "next/server";

export const dynamic = "force-dynamic";

export async function GET(request: NextRequest) {
  try {
    const tenantId = request.nextUrl.searchParams.get("tenant_id") || "default_tenant";
    const res = await proxyBackend(
      `/api/v1/ai-settings?tenant_id=${encodeURIComponent(tenantId)}`,
    );
    return await toNextResponse(res);
  } catch (error) {
    return backendUnavailableResponse(error);
  }
}

export async function PUT(request: NextRequest) {
  try {
    const body = await request.text();
    const res = await proxyBackend("/api/v1/ai-settings", {
      method: "PUT",
      headers: { "Content-Type": "application/json" },
      body,
    });
    return await toNextResponse(res);
  } catch (error) {
    return backendUnavailableResponse(error);
  }
}
