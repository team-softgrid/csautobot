import {
  backendUnavailableResponse,
  proxyBackend,
  toNextResponse,
} from "@/lib/backend";

export const dynamic = "force-dynamic";

export async function GET() {
  try {
    const res = await proxyBackend("/api/v1/users");
    return await toNextResponse(res);
  } catch (error) {
    return backendUnavailableResponse(error);
  }
}

export async function POST(request: Request) {
  try {
    const body = await request.text();
    const res = await proxyBackend("/api/v1/users", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body,
    });
    return await toNextResponse(res);
  } catch (error) {
    return backendUnavailableResponse(error);
  }
}
