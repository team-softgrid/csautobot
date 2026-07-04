import {
  backendUnavailableResponse,
  proxyBackend,
  toNextResponse,
} from "@/lib/backend";

export const dynamic = "force-dynamic";

export async function GET(request: Request) {
  try {
    const { searchParams } = new URL(request.url);
    const tenantId = searchParams.get("tenant_id");
    const query = tenantId
      ? `?tenant_id=${encodeURIComponent(tenantId)}`
      : "";
    const res = await proxyBackend(`/api/v1/billing/admin/plan-audit${query}`);
    return await toNextResponse(res);
  } catch (error) {
    return backendUnavailableResponse(error);
  }
}
