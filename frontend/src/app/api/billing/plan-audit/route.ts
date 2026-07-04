import {
  backendUnavailableResponse,
  proxyBackend,
  toNextResponse,
} from "@/lib/backend";

export const dynamic = "force-dynamic";

export async function GET(request: Request) {
  try {
    const { searchParams } = new URL(request.url);
    const backendQuery = searchParams.toString();
    const path = backendQuery
      ? `/api/v1/billing/admin/plan-audit?${backendQuery}`
      : "/api/v1/billing/admin/plan-audit";
    const res = await proxyBackend(path);
    return await toNextResponse(res);
  } catch (error) {
    return backendUnavailableResponse(error);
  }
}
