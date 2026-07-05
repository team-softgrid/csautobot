import {
  backendUnavailableResponse,
  proxyBackend,
  toNextResponse,
} from "@/lib/backend";
import type { NextRequest } from "next/server";

export const dynamic = "force-dynamic";

export async function POST(request: NextRequest) {
  try {
    const body = await request.text();
    const res = await proxyBackend("/api/v1/ai-settings/test", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body,
    });
    return await toNextResponse(res);
  } catch (error) {
    return backendUnavailableResponse(error);
  }
}
