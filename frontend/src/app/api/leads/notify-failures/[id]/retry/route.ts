import {
  backendUnavailableResponse,
  proxyBackend,
  toNextResponse,
} from "@/lib/backend";

export const dynamic = "force-dynamic";

export async function POST(
  _request: Request,
  { params }: { params: Promise<{ id: string }> },
) {
  try {
    const { id } = await params;
    const res = await proxyBackend(
      `/api/v1/leads/notify-failures/${encodeURIComponent(id)}/retry`,
      { method: "POST" },
    );
    return await toNextResponse(res);
  } catch (error) {
    return backendUnavailableResponse(error);
  }
}
