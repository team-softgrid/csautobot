import {
  backendUnavailableResponse,
  proxyBackend,
  toNextResponse,
} from "@/lib/backend";

export const dynamic = "force-dynamic";

export async function POST(request: Request) {
  try {
    const { searchParams } = new URL(request.url);
    const query = searchParams.toString();
    const path = query
      ? `/api/v1/billing/admin/usage-alerts/notify?${query}`
      : "/api/v1/billing/admin/usage-alerts/notify";
    const res = await proxyBackend(path, { method: "POST" });
    return await toNextResponse(res);
  } catch (error) {
    return backendUnavailableResponse(error);
  }
}
