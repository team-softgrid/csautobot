"use client";

import React, { useEffect, useState } from "react";
import { getApiUrl } from "../utils";

interface FeedbackItem {
  feedback_id: string;
  target_type: string;
  target_id: string;
  role: string;
  reviewer_name: string | null;
  rating: number;
  usefulness: number;
  comment: string | null;
  created_at: string | null;
}

export default function FeedbackPage() {
  const [feedbacks, setFeedbacks] = useState<FeedbackItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetch(`${getApiUrl()}/api/v1/feedbacks`)
      .then((res) => {
        if (!res.ok) throw new Error("피드백 리스트를 조회하지 못했습니다.");
        return res.json();
      })
      .then((data) => {
        setFeedbacks(data);
        setLoading(false);
      })
      .catch((err) => {
        setError(err.message);
        setLoading(false);
      });
  }, []);

  if (loading) {
    return (
      <div style={{ display: "flex", justifyContent: "center", padding: "40px" }}>
        <div className="spinner" style={{ border: "4px solid rgba(255,255,255,0.1)", borderTop: "4px solid #06b6d4", borderRadius: "50%", width: "40px", height: "40px", animation: "spin 1s linear infinite" }} />
      </div>
    );
  }

  return (
    <div style={{ animation: "fadeIn 0.5s ease-out" }}>
      <header style={{ marginBottom: "36px" }}>
        <h2 style={{ fontSize: "28px", fontWeight: "bold", margin: "0 0 8px 0" }}>📬 피드백 모음</h2>
        <p style={{ color: "#94a3b8", margin: 0, fontSize: "14px" }}>
          현장 엔지니어 및 관계자분들이 전해주신 만족도와 의견 모음입니다.
        </p>
      </header>

      {error ? (
        <div className="glass-panel" style={{ padding: "24px", borderLeft: "4px solid #ef4444", color: "#f8fafc" }}>
          <p style={{ margin: 0 }}>오류: {error}</p>
        </div>
      ) : feedbacks.length === 0 ? (
        <div className="glass-panel" style={{ padding: "40px", textAlign: "center", color: "#64748b" }}>
          등록된 피드백이 아직 존재하지 않습니다.
        </div>
      ) : (
        <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fill, minmax(350px, 1fr))", gap: "20px" }}>
          {feedbacks.map((fb) => (
            <div key={fb.feedback_id} className="glass-panel" style={{ padding: "24px" }}>
              <div style={{ display: "flex", justifyContent: "space-between", fontSize: "12px", color: "#94a3b8", marginBottom: "12px" }}>
                <span style={{ background: fb.target_type === "search" ? "rgba(236,72,153,0.15)" : "rgba(59,130,246,0.15)", color: fb.target_type === "search" ? "#ec4899" : "#3b82f6", padding: "2px 6px", borderRadius: "4px", fontWeight: "bold" }}>
                  {fb.target_type === "search" ? "RAG 유사사례 검색" : "점검일지 초안"}
                </span>
                <span>{fb.reviewer_name || "익명"} ({fb.role})</span>
              </div>
              <p style={{ margin: "0 0 16px 0", fontSize: "14px", color: "#f8fafc", lineHeight: "1.6" }}>
                {fb.comment || "(의견 코멘트가 없습니다.)"}
              </p>
              <div style={{ display: "flex", gap: "16px", borderTop: "1px solid rgba(255,255,255,0.06)", paddingTop: "12px", fontSize: "12px", color: "#64748b" }}>
                <span>만족도: <strong style={{ color: "#ec4899" }}>⭐ {fb.rating}점</strong></span>
                <span>도움도: <strong style={{ color: "#3b82f6" }}>💡 {fb.usefulness}점</strong></span>
                {fb.created_at && (
                  <span style={{ marginLeft: "auto" }}>{fb.created_at.slice(0, 10)}</span>
                )}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
