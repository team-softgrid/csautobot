export const DEFAULT_TENANT_ID = "default_tenant";

export function getApiUrl(): string {
  return "";
}

/** Billing/quota API calls use this tenant id (env or localStorage override). */
export function getTenantId(): string {
  if (typeof window !== "undefined") {
    const stored = localStorage.getItem("csautobot_tenant_id");
    if (stored?.trim()) {
      return stored.trim();
    }
  }
  return process.env.NEXT_PUBLIC_TENANT_ID?.trim() || DEFAULT_TENANT_ID;
}

export async function readApiError(response: Response): Promise<string> {
  try {
    const payload = (await response.json()) as { detail?: unknown };
    const { detail } = payload;
    if (typeof detail === "string" && detail.trim()) return detail;
    if (typeof detail === "object" && detail !== null) {
      const d = detail as { message?: unknown; plan_code?: unknown; used?: unknown; limit?: unknown };
      if (typeof d.message === "string" && d.message.trim()) {
        if (response.status === 429 && d.used !== undefined && d.limit !== undefined) {
          return `${d.message} (${String(d.plan_code ?? "")} 플랜: ${d.used}/${d.limit})`;
        }
        return d.message;
      }
    }
  } catch {
    // response body wasn't JSON (or had no detail) — fall through to generic status-based text below
  }
  if (response.status === 429) {
    return "월 사용량 한도를 초과했습니다. 플랜 업그레이드 또는 다음 달까지 대기해 주세요.";
  }
  if (response.status === 503) {
    return "AI 서비스를 일시적으로 사용할 수 없습니다. 잠시 후 다시 시도하거나 관리자에게 문의해 주세요.";
  }
  return `요청 실패 (${response.status})`;
}
