"use client";

import { useCallback, useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { BarChart3, RefreshCw } from "lucide-react";

type UsageFeature = {
  used: number;
  limit: number | null;
  remaining: number | null;
};

type BillingSummary = {
  tenant_id: string;
  plan_code: string;
  period_start: string;
  usage: {
    RAG_SEARCH: UsageFeature;
    AI_GENERATION: UsageFeature;
  };
};

const FEATURE_LABELS: Record<string, string> = {
  RAG_SEARCH: "AS 유사 사례 검색",
  AI_GENERATION: "AI 생성 (점검·견적)",
};

function formatLimit(limit: number | null): string {
  return limit === null ? "무제한" : limit.toLocaleString("ko-KR");
}

async function readError(response: Response): Promise<string> {
  try {
    const payload = (await response.json()) as { detail?: unknown };
    if (typeof payload.detail === "string") return payload.detail;
  } catch {
    // fall through
  }
  if (response.status === 403) return "관리자 권한이 필요합니다.";
  return "요청 처리 중 오류가 발생했습니다.";
}

export default function AdminBillingPage() {
  const router = useRouter();
  const [summary, setSummary] = useState<BillingSummary | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  const clearSessionAndRedirect = useCallback(async () => {
    await fetch("/api/auth/logout", { method: "POST" });
    router.replace("/login");
  }, [router]);

  const fetchSummary = useCallback(async () => {
    setLoading(true);
    setError("");
    try {
      const response = await fetch("/api/billing", { cache: "no-store" });
      if (response.status === 401) {
        await clearSessionAndRedirect();
        return;
      }
      if (!response.ok) {
        throw new Error(await readError(response));
      }
      const data = (await response.json()) as BillingSummary;
      setSummary(data);
    } catch (fetchError) {
      setError(
        fetchError instanceof Error
          ? fetchError.message
          : "사용량 정보를 불러오지 못했습니다.",
      );
    } finally {
      setLoading(false);
    }
  }, [clearSessionAndRedirect]);

  useEffect(() => {
    void fetchSummary();
  }, [fetchSummary]);

  return (
    <div style={{ animation: "fadeIn 0.5s ease-out" }}>
      <header
        style={{
          display: "flex",
          justifyContent: "space-between",
          alignItems: "flex-start",
          marginBottom: "24px",
          gap: "16px",
          flexWrap: "wrap",
        }}
      >
        <div>
          <h2 style={{ fontSize: "28px", fontWeight: "bold", color: "#f8fafc", margin: "0 0 8px" }}>
            과금 · 사용량
          </h2>
          <p style={{ color: "#94a3b8", margin: 0, fontSize: "14px" }}>
            테넌트별 월간 API 사용량과 플랜 한도를 확인합니다.
          </p>
        </div>
        <button
          type="button"
          onClick={() => void fetchSummary()}
          disabled={loading}
          style={{
            display: "inline-flex",
            alignItems: "center",
            gap: "8px",
            padding: "10px 16px",
            borderRadius: "8px",
            border: "1px solid rgba(16,185,129,0.3)",
            background: "rgba(16,185,129,0.1)",
            color: "#10b981",
            cursor: "pointer",
            fontWeight: 600,
          }}
        >
          <RefreshCw size={16} />
          새로고침
        </button>
      </header>

      {error && (
        <div
          className="glass-panel"
          style={{
            padding: "16px",
            marginBottom: "16px",
            borderLeft: "4px solid #ef4444",
            color: "#fca5a5",
          }}
        >
          {error}
        </div>
      )}

      {loading ? (
        <p style={{ color: "#94a3b8" }}>불러오는 중...</p>
      ) : summary ? (
        <>
          <div
            className="glass-panel"
            style={{
              padding: "24px",
              marginBottom: "24px",
              display: "flex",
              gap: "32px",
              flexWrap: "wrap",
            }}
          >
            <div>
              <div style={{ fontSize: "12px", color: "#64748b", marginBottom: "4px" }}>테넌트</div>
              <div style={{ fontSize: "18px", fontWeight: 700, color: "#f8fafc" }}>{summary.tenant_id}</div>
            </div>
            <div>
              <div style={{ fontSize: "12px", color: "#64748b", marginBottom: "4px" }}>플랜</div>
              <div style={{ fontSize: "18px", fontWeight: 700, color: "#06b6d4" }}>{summary.plan_code}</div>
            </div>
            <div>
              <div style={{ fontSize: "12px", color: "#64748b", marginBottom: "4px" }}>집계 시작</div>
              <div style={{ fontSize: "14px", color: "#94a3b8" }}>
                {new Date(summary.period_start).toLocaleDateString("ko-KR")}
              </div>
            </div>
          </div>

          <div
            style={{
              display: "grid",
              gridTemplateColumns: "repeat(auto-fit, minmax(280px, 1fr))",
              gap: "20px",
            }}
          >
            {Object.entries(summary.usage).map(([code, feature]) => {
              const pct =
                feature.limit && feature.limit > 0
                  ? Math.min(100, Math.round((feature.used / feature.limit) * 100))
                  : null;
              return (
                <div key={code} className="glass-panel" style={{ padding: "24px" }}>
                  <div style={{ display: "flex", alignItems: "center", gap: "8px", marginBottom: "16px" }}>
                    <BarChart3 size={18} color="#10b981" />
                    <h3 style={{ margin: 0, fontSize: "16px", color: "#f8fafc" }}>
                      {FEATURE_LABELS[code] || code}
                    </h3>
                  </div>
                  <div style={{ fontSize: "32px", fontWeight: 800, color: "#f8fafc", marginBottom: "8px" }}>
                    {feature.used.toLocaleString("ko-KR")}
                    <span style={{ fontSize: "14px", color: "#64748b", fontWeight: 500 }}>
                      {" "}
                      / {formatLimit(feature.limit)}
                    </span>
                  </div>
                  {pct !== null && (
                    <div
                      style={{
                        height: "8px",
                        borderRadius: "4px",
                        background: "rgba(255,255,255,0.08)",
                        overflow: "hidden",
                        marginBottom: "8px",
                      }}
                    >
                      <div
                        style={{
                          width: `${pct}%`,
                          height: "100%",
                          background: pct >= 90 ? "#ef4444" : "#10b981",
                          borderRadius: "4px",
                        }}
                      />
                    </div>
                  )}
                  <div style={{ fontSize: "13px", color: "#94a3b8" }}>
                    잔여:{" "}
                    {feature.remaining === null
                      ? "무제한"
                      : feature.remaining.toLocaleString("ko-KR")}
                  </div>
                </div>
              );
            })}
          </div>
        </>
      ) : null}
    </div>
  );
}
