import {
  backendUnavailableResponse,
  proxyBackend,
  toNextResponse,
} from "@/lib/backend";
import type { NextRequest } from "next/server";

export const dynamic = "force-dynamic";

export async function GET(request: NextRequest) {
  try {
    const tenantId = request.nextUrl.searchParams.get("tenant_id");
    const path = tenantId
      ? `/api/v1/billing/admin/summary?tenant_id=${encodeURIComponent(tenantId)}`
      : "/api/v1/billing/admin/summary";
    const res = await proxyBackend(path);
    return await toNextResponse(res);
  } catch (error) {
    return backendUnavailableResponse(error);
  }
}
