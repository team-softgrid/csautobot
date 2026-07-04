"use client";

import { useCallback, useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { BarChart3, RefreshCw } from "lucide-react";
import { DEFAULT_TENANT_ID, getTenantId } from "../../utils";

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

type TenantOption = {
  tenant_id: string;
  tenant_name: string;
  plan_code: string;
};

type PlanAuditEntry = {
  audit_id: number;
  tenant_id: string;
  changed_by: string | null;
  old_plan: string | null;
  new_plan: string | null;
  created_at: string | null;
};

type PlanAuditPage = {
  items: PlanAuditEntry[];
  total: number;
  limit: number;
  offset: number;
};

const AUDIT_PAGE_SIZE = 10;

const FEATURE_LABELS: Record<string, string> = {
  RAG_SEARCH: "AS 유사 사례 검색",
  AI_GENERATION: "AI 생성 (점검·견적)",
};

const PLAN_OPTIONS = ["FREE", "PRO", "ENTERPRISE"] as const;
type PlanCode = (typeof PLAN_OPTIONS)[number];

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
  const [tenants, setTenants] = useState<TenantOption[]>([]);
  const [selectedTenantId, setSelectedTenantId] = useState(DEFAULT_TENANT_ID);
  const [summary, setSummary] = useState<BillingSummary | null>(null);
  const [selectedPlan, setSelectedPlan] = useState<PlanCode>("FREE");
  const [savingPlan, setSavingPlan] = useState(false);
  const [notice, setNotice] = useState("");
  const [auditPage, setAuditPage] = useState<PlanAuditPage>({
    items: [],
    total: 0,
    limit: AUDIT_PAGE_SIZE,
    offset: 0,
  });
  const [auditPlanFilter, setAuditPlanFilter] = useState<"" | PlanCode>("");
  const [auditOffset, setAuditOffset] = useState(0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  const clearSessionAndRedirect = useCallback(async () => {
    await fetch("/api/auth/logout", { method: "POST" });
    router.replace("/login");
  }, [router]);

  const fetchAuditLog = useCallback(
    async (tenantId: string, offset: number, newPlan: "" | PlanCode) => {
      try {
        const params = new URLSearchParams({
          tenant_id: tenantId,
          limit: String(AUDIT_PAGE_SIZE),
          offset: String(offset),
        });
        if (newPlan) {
          params.set("new_plan", newPlan);
        }
        const response = await fetch(`/api/billing/plan-audit?${params.toString()}`, {
          cache: "no-store",
        });
        if (response.ok) {
          setAuditPage((await response.json()) as PlanAuditPage);
        }
      } catch {
        setAuditPage({ items: [], total: 0, limit: AUDIT_PAGE_SIZE, offset: 0 });
      }
    },
    [],
  );

  const fetchTenants = useCallback(async () => {
    const response = await fetch("/api/billing/tenants", { cache: "no-store" });
    if (response.status === 401) {
      await clearSessionAndRedirect();
      return [];
    }
    if (!response.ok) {
      throw new Error(await readError(response));
    }
    return (await response.json()) as TenantOption[];
  }, [clearSessionAndRedirect]);

  const fetchSummary = useCallback(
    async (tenantId: string) => {
      setLoading(true);
      setError("");
      try {
        const response = await fetch(
          `/api/billing?tenant_id=${encodeURIComponent(tenantId)}`,
          { cache: "no-store" },
        );
        if (response.status === 401) {
          await clearSessionAndRedirect();
          return;
        }
        if (!response.ok) {
          throw new Error(await readError(response));
        }
        const data = (await response.json()) as BillingSummary;
        setSummary(data);
        setSelectedPlan(data.plan_code as PlanCode);
      } catch (fetchError) {
        setSummary(null);
        setError(
          fetchError instanceof Error
            ? fetchError.message
            : "사용량 정보를 불러오지 못했습니다.",
        );
      } finally {
        setLoading(false);
      }
    },
    [clearSessionAndRedirect],
  );

  useEffect(() => {
    const initialTenant = getTenantId();
    setSelectedTenantId(initialTenant);
    void (async () => {
      try {
        const list = await fetchTenants();
        setTenants(list);
        const exists = list.some((t) => t.tenant_id === initialTenant);
        const tenantId = exists ? initialTenant : list[0]?.tenant_id || DEFAULT_TENANT_ID;
        setSelectedTenantId(tenantId);
        await fetchSummary(tenantId);
        await fetchAuditLog(tenantId, 0, "");
      } catch (fetchError) {
        setError(
          fetchError instanceof Error
            ? fetchError.message
            : "테넌트 목록을 불러오지 못했습니다.",
        );
        setLoading(false);
      }
    })();
  }, [fetchTenants, fetchSummary, fetchAuditLog]);

  const handleTenantChange = (tenantId: string) => {
    setSelectedTenantId(tenantId);
    setAuditOffset(0);
    setAuditPlanFilter("");
    if (typeof window !== "undefined") {
      localStorage.setItem("csautobot_tenant_id", tenantId);
    }
    void fetchSummary(tenantId);
    void fetchAuditLog(tenantId, 0, "");
  };

  const handleAuditFilterChange = (plan: "" | PlanCode) => {
    setAuditPlanFilter(plan);
    setAuditOffset(0);
    void fetchAuditLog(selectedTenantId, 0, plan);
  };

  const handleAuditPageChange = (nextOffset: number) => {
    setAuditOffset(nextOffset);
    void fetchAuditLog(selectedTenantId, nextOffset, auditPlanFilter);
  };

  const handlePlanSave = async () => {
    setSavingPlan(true);
    setError("");
    setNotice("");
    try {
      const response = await fetch(
        `/api/billing/tenants/${encodeURIComponent(selectedTenantId)}/plan`,
        {
          method: "PATCH",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ plan_code: selectedPlan }),
        },
      );
      if (!response.ok) {
        throw new Error(await readError(response));
      }
      setNotice("플랜이 변경되었습니다.");
      const list = await fetchTenants();
      setTenants(list);
      await fetchSummary(selectedTenantId);
      setAuditOffset(0);
      await fetchAuditLog(selectedTenantId, 0, auditPlanFilter);
    } catch (saveError) {
      setError(
        saveError instanceof Error ? saveError.message : "플랜 변경에 실패했습니다.",
      );
    } finally {
      setSavingPlan(false);
    }
  };

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
        <div style={{ display: "flex", gap: "12px", flexWrap: "wrap", alignItems: "center" }}>
          <select
            value={selectedTenantId}
            onChange={(e) => handleTenantChange(e.target.value)}
            disabled={loading || tenants.length === 0}
            style={{
              background: "rgba(255,255,255,0.05)",
              border: "1px solid rgba(255,255,255,0.1)",
              borderRadius: "8px",
              color: "#f8fafc",
              padding: "10px 14px",
              minWidth: "220px",
            }}
          >
            {tenants.length === 0 ? (
              <option value={selectedTenantId}>{selectedTenantId}</option>
            ) : (
              tenants.map((tenant) => (
                <option key={tenant.tenant_id} value={tenant.tenant_id}>
                  {tenant.tenant_name} ({tenant.tenant_id}) — {tenant.plan_code}
                </option>
              ))
            )}
          </select>
          <button
            type="button"
            onClick={() => void fetchSummary(selectedTenantId)}
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
        </div>
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

      {notice && (
        <div
          className="glass-panel"
          style={{
            padding: "16px",
            marginBottom: "16px",
            borderLeft: "4px solid #10b981",
            color: "#86efac",
          }}
        >
          {notice}
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
              <div style={{ display: "flex", gap: "8px", alignItems: "center", flexWrap: "wrap" }}>
                <select
                  value={selectedPlan}
                  onChange={(e) => setSelectedPlan(e.target.value as PlanCode)}
                  disabled={savingPlan}
                  style={{
                    background: "rgba(255,255,255,0.05)",
                    border: "1px solid rgba(255,255,255,0.1)",
                    borderRadius: "8px",
                    color: "#06b6d4",
                    padding: "8px 12px",
                    fontWeight: 700,
                  }}
                >
                  {PLAN_OPTIONS.map((plan) => (
                    <option key={plan} value={plan}>
                      {plan}
                    </option>
                  ))}
                </select>
                <button
                  type="button"
                  onClick={() => void handlePlanSave()}
                  disabled={savingPlan || selectedPlan === summary.plan_code}
                  style={{
                    padding: "8px 14px",
                    borderRadius: "8px",
                    border: "1px solid rgba(6,182,212,0.3)",
                    background: "rgba(6,182,212,0.1)",
                    color: "#06b6d4",
                    cursor: "pointer",
                    fontWeight: 600,
                  }}
                >
                  {savingPlan ? "저장 중..." : "플랜 저장"}
                </button>
              </div>
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

      {auditPage.total > 0 || auditPlanFilter ? (
        <section className="glass-panel" style={{ padding: "24px", marginTop: "24px" }}>
          <div
            style={{
              display: "flex",
              justifyContent: "space-between",
              alignItems: "center",
              gap: "12px",
              flexWrap: "wrap",
              marginBottom: "12px",
            }}
          >
            <h3 style={{ margin: 0, color: "#f8fafc", fontSize: "16px" }}>
              플랜 변경 감사 로그
            </h3>
            <select
              value={auditPlanFilter}
              onChange={(e) => handleAuditFilterChange(e.target.value as "" | PlanCode)}
              style={{
                background: "rgba(255,255,255,0.05)",
                border: "1px solid rgba(255,255,255,0.1)",
                borderRadius: "8px",
                color: "#f8fafc",
                padding: "8px 12px",
              }}
            >
              <option value="">전체 플랜</option>
              {PLAN_OPTIONS.map((plan) => (
                <option key={plan} value={plan}>
                  {plan} 로 변경
                </option>
              ))}
            </select>
          </div>
          {auditPage.items.length === 0 ? (
            <p style={{ color: "#94a3b8", margin: 0 }}>조건에 맞는 감사 로그가 없습니다.</p>
          ) : (
            <div style={{ overflowX: "auto" }}>
              <table style={{ width: "100%", borderCollapse: "collapse", fontSize: "13px" }}>
                <thead>
                  <tr style={{ borderBottom: "1px solid rgba(255,255,255,0.08)", color: "#94a3b8" }}>
                    <th style={{ padding: "10px 12px", textAlign: "left" }}>변경자</th>
                    <th style={{ padding: "10px 12px", textAlign: "left" }}>이전</th>
                    <th style={{ padding: "10px 12px", textAlign: "left" }}>변경</th>
                    <th style={{ padding: "10px 12px", textAlign: "left" }}>시각</th>
                  </tr>
                </thead>
                <tbody>
                  {auditPage.items.map((entry) => (
                    <tr key={entry.audit_id} style={{ borderBottom: "1px solid rgba(255,255,255,0.05)" }}>
                      <td style={{ padding: "10px 12px", color: "#e2e8f0" }}>
                        {entry.changed_by || "-"}
                      </td>
                      <td style={{ padding: "10px 12px", color: "#94a3b8" }}>{entry.old_plan}</td>
                      <td style={{ padding: "10px 12px", color: "#06b6d4", fontWeight: 600 }}>
                        {entry.new_plan}
                      </td>
                      <td style={{ padding: "10px 12px", color: "#94a3b8", whiteSpace: "nowrap" }}>
                        {entry.created_at
                          ? new Date(entry.created_at).toLocaleString("ko-KR")
                          : "-"}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
          {auditPage.total > AUDIT_PAGE_SIZE && (
            <div
              style={{
                display: "flex",
                justifyContent: "space-between",
                alignItems: "center",
                marginTop: "16px",
                gap: "12px",
              }}
            >
              <span style={{ color: "#94a3b8", fontSize: "13px" }}>
                {auditPage.total.toLocaleString("ko-KR")}건 중{" "}
                {auditOffset + 1}–{Math.min(auditOffset + AUDIT_PAGE_SIZE, auditPage.total)}
              </span>
              <div style={{ display: "flex", gap: "8px" }}>
                <button
                  type="button"
                  disabled={auditOffset === 0}
                  onClick={() => handleAuditPageChange(Math.max(0, auditOffset - AUDIT_PAGE_SIZE))}
                  style={{
                    padding: "6px 12px",
                    borderRadius: "6px",
                    border: "1px solid rgba(255,255,255,0.1)",
                    background: "rgba(255,255,255,0.05)",
                    color: "#e2e8f0",
                    cursor: auditOffset === 0 ? "not-allowed" : "pointer",
                  }}
                >
                  이전
                </button>
                <button
                  type="button"
                  disabled={auditOffset + AUDIT_PAGE_SIZE >= auditPage.total}
                  onClick={() => handleAuditPageChange(auditOffset + AUDIT_PAGE_SIZE)}
                  style={{
                    padding: "6px 12px",
                    borderRadius: "6px",
                    border: "1px solid rgba(255,255,255,0.1)",
                    background: "rgba(255,255,255,0.05)",
                    color: "#e2e8f0",
                    cursor:
                      auditOffset + AUDIT_PAGE_SIZE >= auditPage.total
                        ? "not-allowed"
                        : "pointer",
                  }}
                >
                  다음
                </button>
              </div>
            </div>
          )}
        </section>
      ) : null}
    </div>
  );
}
