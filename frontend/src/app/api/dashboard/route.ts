import {
  backendUnavailableResponse,
  proxyBackend,
  toNextResponse,
} from "@/lib/backend";

export const dynamic = "force-dynamic";

export async function GET() {
  try {
    const res = await proxyBackend("/api/v1/dashboard/stats");
    return await toNextResponse(res);
  } catch (error) {
    return backendUnavailableResponse(error);
  }
}
