"use client";

import React, { useEffect, useState } from "react";
import { getApiUrl } from "../utils";

interface MetricSummary {
  total_inspections: number;
  completed_inspections: number;
  draft_inspections: number;
  total_feedbacks: number;
  avg_rating: number;
  avg_usefulness: number;
}

interface DashboardData {
  metrics: MetricSummary;
  inspections: any[];
  feedbacks: any[];
}

export default function DashboardPage() {
  const [data, setData] = useState<DashboardData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetch(`${getApiUrl()}/api/v1/dashboard/stats`)
      .then((res) => {
        if (!res.ok) throw new Error("대시보드 통계 정보를 가져오지 못했습니다.");
        return res.json();
      })
      .then((json) => {
        setData(json);
        setLoading(false);
      })
      .catch((err) => {
        setError(err.message);
        setLoading(false);
      });
  }, []);

  if (loading) {
    return (
      <div style={{ display: "flex", justifyContent: "center", alignItems: "center", minHeight: "50vh" }}>
        <div className="spinner" style={{ border: "4px solid rgba(255,255,255,0.1)", borderTop: "4px solid #06b6d4", borderRadius: "50%", width: "40px", height: "40px", animation: "spin 1s linear infinite" }} />
      </div>
    );
  }

  if (error || !data) {
    return (
      <div className="glass-panel" style={{ padding: "32px", borderLeft: "4px solid #ef4444", color: "#f8fafc" }}>
        <h3 style={{ margin: "0 0 8px 0" }}>⚠️ 오류가 발생했습니다</h3>
        <p style={{ margin: 0, color: "#94a3b8" }}>{error || "데이터를 불러올 수 없습니다."}</p>
      </div>
    );
  }

  const { metrics, inspections, feedbacks } = data;

  // Calculate risk counts
  const riskCounts = inspections.reduce(
    (acc: any, curr: any) => {
      const risk = curr.overall_risk || "low";
      acc[risk] = (acc[risk] || 0) + 1;
      return acc;
    },
    { high: 0, mid: 0, low: 0 }
  );

  const totalRisks = (riskCounts.high + riskCounts.mid + riskCounts.low) || 1;
  const highPercent = Math.round((riskCounts.high / totalRisks) * 100);
  const midPercent = Math.round((riskCounts.mid / totalRisks) * 100);
  const lowPercent = Math.round((riskCounts.low / totalRisks) * 100);

  return (
    <div style={{ animation: "fadeIn 0.5s ease-out" }}>
      <header style={{ marginBottom: "36px" }}>
        <h2 style={{ fontSize: "28px", fontWeight: "bold", margin: "0 0 8px 0" }}>📊 운영 대시보드</h2>
        <p style={{ color: "#94a3b8", margin: 0, fontSize: "14px" }}>
          현장 충전기 점검 위험도 통계 및 엔지니어 피드백 데이터 요약입니다.
        </p>
      </header>

      {/* Metrics Row */}
      <section style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(220px, 1fr))", gap: "20px", marginBottom: "36px" }}>
        <div className="glass-panel" style={{ padding: "24px", borderLeft: "4px solid #06b6d4" }}>
          <div style={{ fontSize: "13px", color: "#94a3b8", fontWeight: "bold" }}>총 점검일지</div>
          <div style={{ fontSize: "32px", fontWeight: "bold", marginTop: "8px", color: "#f8fafc" }}>{metrics.total_inspections}건</div>
        </div>
        <div className="glass-panel" style={{ padding: "24px", borderLeft: "4px solid #10b981" }}>
          <div style={{ fontSize: "13px", color: "#94a3b8", fontWeight: "bold" }}>확정 완료</div>
          <div style={{ fontSize: "32px", fontWeight: "bold", marginTop: "8px", color: "#10b981" }}>{metrics.completed_inspections}건</div>
        </div>
        <div className="glass-panel" style={{ padding: "24px", borderLeft: "4px solid #f59e0b" }}>
          <div style={{ fontSize: "13px", color: "#94a3b8", fontWeight: "bold" }}>작성중 임시초안</div>
          <div style={{ fontSize: "32px", fontWeight: "bold", marginTop: "8px", color: "#f59e0b" }}>{metrics.draft_inspections}건</div>
        </div>
        <div className="glass-panel" style={{ padding: "24px", borderLeft: "4px solid #ec4899" }}>
          <div style={{ fontSize: "13px", color: "#94a3b8", fontWeight: "bold" }}>평균 평점 (만족도)</div>
          <div style={{ fontSize: "32px", fontWeight: "bold", marginTop: "8px", color: "#ec4899" }}>⭐ {metrics.avg_rating} / 5.0</div>
        </div>
      </section>

      {/* Main Charts and Tables Grid */}
      <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(450px, 1fr))", gap: "24px" }}>
        
        {/* Risk Distribution Chart */}
        <section className="glass-panel" style={{ padding: "32px" }}>
          <h3 style={{ fontSize: "18px", fontWeight: "bold", margin: "0 0 24px 0", color: "#f8fafc" }}>🚨 점검 현황 위험도 분포</h3>
          <div style={{ display: "flex", flexDirection: "column", gap: "20px" }}>
            {/* High */}
            <div>
              <div style={{ display: "flex", justifyContent: "space-between", marginBottom: "8px", fontSize: "13px" }}>
                <span style={{ color: "#ef4444", fontWeight: "bold" }}>High (고위험/이상)</span>
                <span>{riskCounts.high}건 ({highPercent}%)</span>
              </div>
              <div style={{ height: "12px", background: "rgba(255,255,255,0.06)", borderRadius: "6px", overflow: "hidden" }}>
                <div style={{ width: `${highPercent}%`, height: "100%", background: "#ef4444", borderRadius: "6px", transition: "width 0.5s" }} />
              </div>
            </div>

            {/* Mid */}
            <div>
              <div style={{ display: "flex", justifyContent: "space-between", marginBottom: "8px", fontSize: "13px" }}>
                <span style={{ color: "#f59e0b", fontWeight: "bold" }}>Mid (주의필요)</span>
                <span>{riskCounts.mid}건 ({midPercent}%)</span>
              </div>
              <div style={{ height: "12px", background: "rgba(255,255,255,0.06)", borderRadius: "6px", overflow: "hidden" }}>
                <div style={{ width: `${midPercent}%`, height: "100%", background: "#f59e0b", borderRadius: "6px", transition: "width 0.5s" }} />
              </div>
            </div>

            {/* Low */}
            <div>
              <div style={{ display: "flex", justifyContent: "space-between", marginBottom: "8px", fontSize: "13px" }}>
                <span style={{ color: "#10b981", fontWeight: "bold" }}>Low (정상)</span>
                <span>{riskCounts.low}건 ({lowPercent}%)</span>
              </div>
              <div style={{ height: "12px", background: "rgba(255,255,255,0.06)", borderRadius: "6px", overflow: "hidden" }}>
                <div style={{ width: `${lowPercent}%`, height: "100%", background: "#10b981", borderRadius: "6px", transition: "width 0.5s" }} />
              </div>
            </div>
          </div>
        </section>

        {/* Feedbacks Panel */}
        <section className="glass-panel" style={{ padding: "32px", maxHeight: "350px", overflowY: "auto" }}>
          <h3 style={{ fontSize: "18px", fontWeight: "bold", margin: "0 0 20px 0", color: "#f8fafc" }}>📬 최신 현장 피드백</h3>
          {feedbacks.length === 0 ? (
            <div style={{ color: "#64748b", textAlign: "center", padding: "20px" }}>등록된 피드백이 없습니다.</div>
          ) : (
            <div style={{ display: "flex", flexDirection: "column", gap: "16px" }}>
              {feedbacks.slice(0, 5).map((fb, idx) => (
                <div key={idx} style={{ background: "rgba(255,255,255,0.03)", padding: "16px", borderRadius: "8px", border: "1px solid rgba(255,255,255,0.04)" }}>
                  <div style={{ display: "flex", justifyContent: "space-between", fontSize: "12px", color: "#94a3b8", marginBottom: "8px" }}>
                    <span>{fb.role} ({fb.target_type === "search" ? "RAG검색" : "점검일지"})</span>
                    <span>⭐ {fb.rating}점 / 업무도움 {fb.usefulness}점</span>
                  </div>
                  <p style={{ margin: 0, fontSize: "13px", color: "#f8fafc", lineHeight: "1.5" }}>
                    {fb.comment || "(코멘트 없음)"}
                  </p>
                </div>
              ))}
            </div>
          )}
        </section>
      </div>

      {/* Recent Inspections Table */}
      <section className="glass-panel" style={{ padding: "32px", marginTop: "24px" }}>
        <h3 style={{ fontSize: "18px", fontWeight: "bold", margin: "0 0 20px 0", color: "#f8fafc" }}>📝 최근 점검 일지 목록</h3>
        <div style={{ overflowX: "auto" }}>
          <table style={{ width: "100%", borderCollapse: "collapse", fontSize: "14px", textAlign: "left" }}>
            <thead>
              <tr style={{ borderBottom: "1px solid rgba(255,255,255,0.08)", color: "#94a3b8" }}>
                <th style={{ padding: "12px 8px" }}>일지 ID</th>
                <th style={{ padding: "12px 8px" }}>점검처</th>
                <th style={{ padding: "12px 8px" }}>대상</th>
                <th style={{ padding: "12px 8px" }}>구분</th>
                <th style={{ padding: "12px 8px" }}>위험도</th>
                <th style={{ padding: "12px 8px" }}>상태</th>
                <th style={{ padding: "12px 8px" }}>생성일</th>
              </tr>
            </thead>
            <tbody>
              {inspections.slice(0, 10).map((log, i) => (
                <tr key={i} style={{ borderBottom: "1px solid rgba(255,255,255,0.04)", transition: "background 0.2s" }} onMouseEnter={(e) => e.currentTarget.style.background = "rgba(255,255,255,0.02)"} onMouseLeave={(e) => e.currentTarget.style.background = "transparent"}>
                  <td style={{ padding: "16px 8px", color: "#06b6d4", fontFamily: "monospace" }}>{log.inspection_id}</td>
                  <td style={{ padding: "16px 8px", fontWeight: "bold" }}>{log.site_name}</td>
                  <td style={{ padding: "16px 8px" }}>{log.charger_id !== "-" ? "충전기" : "-"}</td>
                  <td style={{ padding: "16px 8px" }}>{log.inspection_type} ({log.inspection_cycle})</td>
                  <td style={{ padding: "16px 8px" }}>
                    <span style={{
                      padding: "4px 8px",
                      borderRadius: "4px",
                      fontSize: "12px",
                      fontWeight: "bold",
                      background: log.overall_risk === "high" ? "rgba(239, 68, 68, 0.15)" : log.overall_risk === "mid" ? "rgba(245, 158, 11, 0.15)" : "rgba(16, 185, 129, 0.15)",
                      color: log.overall_risk === "high" ? "#ef4444" : log.overall_risk === "mid" ? "#f59e0b" : "#10b981"
                    }}>
                      {log.overall_risk.toUpperCase()}
                    </span>
                  </td>
                  <td style={{ padding: "16px 8px" }}>
                    <span style={{
                      color: log.status === "confirmed" ? "#10b981" : "#94a3b8"
                    }}>
                      {log.status === "confirmed" ? "확정완료" : "초안임시"}
                    </span>
                  </td>
                  <td style={{ padding: "16px 8px", color: "#64748b" }}>
                    {log.created_at ? log.created_at.slice(0, 10) : "-"}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>
    </div>
  );
}
