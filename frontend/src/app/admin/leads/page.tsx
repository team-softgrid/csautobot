"use client";

import { useCallback, useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { Mail, Phone, RefreshCw } from "lucide-react";

type LeadStatus = "NEW" | "CONTACTED" | "CLOSED";

type NotifyFailure = {
  id: number;
  lead_id: number | null;
  channel: string;
  error_message: string;
  created_at: number;
};

type NotifyChannelStatus = {
  channel: string;
  label: string;
  configured: boolean;
  env_var: string;
};

type Lead = {
  id: number;
  company_name: string;
  contact_name: string;
  email: string;
  phone?: string | null;
  interest_plans: string;
  message?: string | null;
  status: LeadStatus;
  created_at: number;
};

const STATUS_LABELS: Record<LeadStatus, string> = {
  NEW: "신규",
  CONTACTED: "연락 완료",
  CLOSED: "종료",
};

function formatDate(epochSeconds: number): string {
  return new Intl.DateTimeFormat("ko-KR", {
    dateStyle: "medium",
    timeStyle: "short",
  }).format(new Date(epochSeconds * 1000));
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

export default function AdminLeadsPage() {
  const router = useRouter();
  const [leads, setLeads] = useState<Lead[]>([]);
  const [failures, setFailures] = useState<NotifyFailure[]>([]);
  const [channels, setChannels] = useState<NotifyChannelStatus[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [updatingId, setUpdatingId] = useState<number | null>(null);
  const [retryingId, setRetryingId] = useState<number | null>(null);
  const [testingChannel, setTestingChannel] = useState<string | null>(null);
  const [dryRun, setDryRun] = useState(true);
  const [testNotice, setTestNotice] = useState("");

  const fetchFailures = useCallback(async () => {
    try {
      const response = await fetch("/api/leads/notify-failures", { cache: "no-store" });
      if (response.ok) {
        setFailures((await response.json()) as NotifyFailure[]);
      }
    } catch {
      // optional section — ignore fetch errors
    }
  }, []);

  const clearSessionAndRedirect = useCallback(async () => {
    await fetch("/api/auth/logout", { method: "POST" });
    router.replace("/login");
  }, [router]);

  const fetchLeads = useCallback(async () => {
    setLoading(true);
    setError("");
    try {
      const response = await fetch("/api/leads", { cache: "no-store" });
      if (response.status === 401) {
        await clearSessionAndRedirect();
        return;
      }
      if (!response.ok) {
        throw new Error(await readError(response));
      }
      const data = (await response.json()) as Lead[];
      setLeads(data);
    } catch (fetchError) {
      setError(
        fetchError instanceof Error
          ? fetchError.message
          : "상담 목록을 불러오지 못했습니다.",
      );
    } finally {
      setLoading(false);
    }
  }, [clearSessionAndRedirect]);

  useEffect(() => {
    void (async () => {
      await fetchLeads();
      await fetchFailures();
      try {
        const response = await fetch("/api/leads/notify-channels", { cache: "no-store" });
        if (response.ok) {
          setChannels((await response.json()) as NotifyChannelStatus[]);
        }
      } catch {
        // optional section
      }
    })();
  }, [fetchLeads, fetchFailures]);

  const retryFailure = async (failure: NotifyFailure) => {
    setRetryingId(failure.id);
    setError("");
    try {
      const response = await fetch(`/api/leads/notify-failures/${failure.id}/retry`, {
        method: "POST",
      });
      if (!response.ok) {
        throw new Error(await readError(response));
      }
      const result = (await response.json()) as { success: boolean; message: string };
      if (!result.success) {
        setError(result.message);
      }
      await fetchFailures();
    } catch (retryError) {
      setError(
        retryError instanceof Error ? retryError.message : "알림 재전송에 실패했습니다.",
      );
    } finally {
      setRetryingId(null);
    }
  };

  const testChannel = async (channel: string) => {
    setTestingChannel(channel);
    setError("");
    setTestNotice("");
    try {
      const response = await fetch("/api/leads/notify-test", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ channel, dry_run: dryRun }),
      });
      if (!response.ok) {
        throw new Error(await readError(response));
      }
      const result = (await response.json()) as {
        success: boolean;
        message: string;
        dry_run: boolean;
      };
      setTestNotice(
        result.success
          ? `${result.dry_run ? "[Dry-run] " : ""}${result.message}`
          : result.message,
      );
      if (!result.success) {
        setError(result.message);
      }
    } catch (testError) {
      setError(
        testError instanceof Error ? testError.message : "테스트 발송에 실패했습니다.",
      );
    } finally {
      setTestingChannel(null);
    }
  };

  const updateStatus = async (lead: Lead, status: LeadStatus) => {
    setUpdatingId(lead.id);
    setError("");
    try {
      const response = await fetch(`/api/leads/${lead.id}`, {
        method: "PATCH",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ status }),
      });
      if (!response.ok) {
        throw new Error(await readError(response));
      }
      await fetchLeads();
    } catch (updateError) {
      setError(
        updateError instanceof Error
          ? updateError.message
          : "상태 변경에 실패했습니다.",
      );
    } finally {
      setUpdatingId(null);
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
            도입 상담 리드
          </h2>
          <p style={{ color: "#94a3b8", margin: 0, fontSize: "14px" }}>
            랜딩 Contact 폼으로 접수된 B2B 도입 문의를 관리합니다.
          </p>
        </div>
        <button
          type="button"
          onClick={() => void fetchLeads()}
          disabled={loading}
          style={{
            display: "inline-flex",
            alignItems: "center",
            gap: "8px",
            padding: "10px 16px",
            borderRadius: "8px",
            border: "1px solid rgba(6,182,212,0.3)",
            background: "rgba(6,182,212,0.1)",
            color: "#06b6d4",
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

      {testNotice && (
        <div
          className="glass-panel"
          style={{
            padding: "16px",
            marginBottom: "16px",
            borderLeft: "4px solid #10b981",
            color: "#86efac",
          }}
        >
          {testNotice}
        </div>
      )}

      {channels.length > 0 && (
        <section
          className="glass-panel"
          style={{ padding: "20px 24px", marginBottom: "20px" }}
        >
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
              알림 채널 설정 상태
            </h3>
            <label style={{ display: "flex", alignItems: "center", gap: "8px", color: "#94a3b8", fontSize: "13px" }}>
              <input
                type="checkbox"
                checked={dryRun}
                onChange={(e) => setDryRun(e.target.checked)}
              />
              Dry-run (설정 확인만)
            </label>
          </div>
          <div style={{ display: "flex", gap: "12px", flexWrap: "wrap" }}>
            {channels.map((ch) => (
              <div
                key={ch.channel}
                style={{
                  padding: "10px 14px",
                  borderRadius: "8px",
                  border: `1px solid ${ch.configured ? "rgba(16,185,129,0.3)" : "rgba(239,68,68,0.3)"}`,
                  background: ch.configured ? "rgba(16,185,129,0.08)" : "rgba(239,68,68,0.08)",
                  minWidth: "180px",
                }}
              >
                <div style={{ fontWeight: 600, color: "#f8fafc", fontSize: "14px" }}>
                  {ch.label}
                </div>
                <div
                  style={{
                    fontSize: "12px",
                    marginTop: "4px",
                    color: ch.configured ? "#86efac" : "#fca5a5",
                  }}
                >
                  {ch.configured ? "설정됨" : "미설정"}
                </div>
                <div style={{ fontSize: "11px", color: "#64748b", marginTop: "4px" }}>
                  {ch.env_var}
                </div>
                <button
                  type="button"
                  disabled={testingChannel === ch.channel}
                  onClick={() => void testChannel(ch.channel)}
                  style={{
                    marginTop: "8px",
                    padding: "5px 10px",
                    borderRadius: "6px",
                    border: "1px solid rgba(6,182,212,0.3)",
                    background: "rgba(6,182,212,0.1)",
                    color: "#06b6d4",
                    cursor: "pointer",
                    fontSize: "12px",
                    fontWeight: 600,
                  }}
                >
                  {testingChannel === ch.channel ? "테스트 중..." : "테스트"}
                </button>
              </div>
            ))}
          </div>
        </section>
      )}

      <div className="glass-panel" style={{ padding: "0", overflow: "hidden" }}>
        {loading ? (
          <p style={{ padding: "24px", color: "#94a3b8" }}>불러오는 중...</p>
        ) : leads.length === 0 ? (
          <p style={{ padding: "24px", color: "#94a3b8" }}>접수된 상담 요청이 없습니다.</p>
        ) : (
          <div style={{ overflowX: "auto" }}>
            <table style={{ width: "100%", borderCollapse: "collapse", fontSize: "14px" }}>
              <thead>
                <tr style={{ borderBottom: "1px solid rgba(255,255,255,0.08)", color: "#94a3b8" }}>
                  <th style={{ padding: "14px 16px", textAlign: "left" }}>회사</th>
                  <th style={{ padding: "14px 16px", textAlign: "left" }}>담당자</th>
                  <th style={{ padding: "14px 16px", textAlign: "left" }}>연락처</th>
                  <th style={{ padding: "14px 16px", textAlign: "left" }}>관심 플랜</th>
                  <th style={{ padding: "14px 16px", textAlign: "left" }}>접수일</th>
                  <th style={{ padding: "14px 16px", textAlign: "left" }}>상태</th>
                </tr>
              </thead>
              <tbody>
                {leads.map((lead) => (
                  <tr
                    key={lead.id}
                    style={{ borderBottom: "1px solid rgba(255,255,255,0.05)" }}
                  >
                    <td style={{ padding: "14px 16px", color: "#f8fafc", fontWeight: 600 }}>
                      {lead.company_name}
                      {lead.message && (
                        <div style={{ fontSize: "12px", color: "#64748b", marginTop: "4px", maxWidth: "240px" }}>
                          {lead.message}
                        </div>
                      )}
                    </td>
                    <td style={{ padding: "14px 16px", color: "#e2e8f0" }}>{lead.contact_name}</td>
                    <td style={{ padding: "14px 16px", color: "#cbd5e1" }}>
                      <div style={{ display: "flex", alignItems: "center", gap: "6px" }}>
                        <Mail size={14} />
                        {lead.email}
                      </div>
                      {lead.phone && (
                        <div style={{ display: "flex", alignItems: "center", gap: "6px", marginTop: "4px" }}>
                          <Phone size={14} />
                          {lead.phone}
                        </div>
                      )}
                    </td>
                    <td style={{ padding: "14px 16px", color: "#94a3b8", fontSize: "13px" }}>
                      {lead.interest_plans || "-"}
                    </td>
                    <td style={{ padding: "14px 16px", color: "#94a3b8", whiteSpace: "nowrap" }}>
                      {formatDate(lead.created_at)}
                    </td>
                    <td style={{ padding: "14px 16px" }}>
                      <select
                        value={lead.status}
                        disabled={updatingId === lead.id}
                        onChange={(e) => void updateStatus(lead, e.target.value as LeadStatus)}
                        style={{
                          background: "rgba(255,255,255,0.05)",
                          border: "1px solid rgba(255,255,255,0.1)",
                          borderRadius: "6px",
                          color: "#f8fafc",
                          padding: "6px 10px",
                        }}
                      >
                        {(Object.keys(STATUS_LABELS) as LeadStatus[]).map((status) => (
                          <option key={status} value={status}>
                            {STATUS_LABELS[status]}
                          </option>
                        ))}
                      </select>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {failures.length > 0 && (
        <section className="glass-panel" style={{ padding: "24px", marginTop: "24px" }}>
          <h3 style={{ margin: "0 0 12px", color: "#f8fafc", fontSize: "16px" }}>
            알림 실패 로그 (dead-letter)
          </h3>
          <div style={{ overflowX: "auto" }}>
            <table style={{ width: "100%", borderCollapse: "collapse", fontSize: "13px" }}>
              <thead>
                <tr style={{ borderBottom: "1px solid rgba(255,255,255,0.08)", color: "#94a3b8" }}>
                  <th style={{ padding: "10px 12px", textAlign: "left" }}>Lead ID</th>
                  <th style={{ padding: "10px 12px", textAlign: "left" }}>채널</th>
                  <th style={{ padding: "10px 12px", textAlign: "left" }}>오류</th>
                  <th style={{ padding: "10px 12px", textAlign: "left" }}>시각</th>
                  <th style={{ padding: "10px 12px", textAlign: "left" }}>재전송</th>
                </tr>
              </thead>
              <tbody>
                {failures.map((row) => (
                  <tr key={row.id} style={{ borderBottom: "1px solid rgba(255,255,255,0.05)" }}>
                    <td style={{ padding: "10px 12px", color: "#e2e8f0" }}>{row.lead_id ?? "-"}</td>
                    <td style={{ padding: "10px 12px", color: "#94a3b8" }}>{row.channel}</td>
                    <td style={{ padding: "10px 12px", color: "#fca5a5", maxWidth: "360px" }}>{row.error_message}</td>
                    <td style={{ padding: "10px 12px", color: "#94a3b8", whiteSpace: "nowrap" }}>
                      {formatDate(row.created_at)}
                    </td>
                    <td style={{ padding: "10px 12px" }}>
                      <button
                        type="button"
                        disabled={retryingId === row.id || !row.lead_id}
                        onClick={() => void retryFailure(row)}
                        style={{
                          padding: "6px 12px",
                          borderRadius: "6px",
                          border: "1px solid rgba(6,182,212,0.3)",
                          background: "rgba(6,182,212,0.1)",
                          color: "#06b6d4",
                          cursor: "pointer",
                          fontSize: "12px",
                          fontWeight: 600,
                        }}
                      >
                        {retryingId === row.id ? "전송 중..." : "재전송"}
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </section>
      )}
    </div>
  );
}
