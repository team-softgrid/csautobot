import {
  backendUnavailableResponse,
  proxyBackend,
  toNextResponse,
} from "@/lib/backend";

export const dynamic = "force-dynamic";

export async function PATCH(
  request: Request,
  context: { params: Promise<{ id: string }> },
) {
  try {
    const { id } = await context.params;
    const body = await request.text();
    const res = await proxyBackend(`/api/v1/leads/${id}`, {
      method: "PATCH",
      headers: { "Content-Type": "application/json" },
      body,
    });
    return await toNextResponse(res);
  } catch (error) {
    return backendUnavailableResponse(error);
  }
}
