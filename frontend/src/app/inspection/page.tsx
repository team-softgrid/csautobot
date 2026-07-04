"use client";

import React, { useEffect, useState } from "react";
import { getApiUrl, getTenantId, readApiError } from "../utils";

interface ChecklistItem {
  item: string;
  status: string;
  note: string;
}

export default function InspectionPage() {
  const [inspectionId, setInspectionId] = useState("");
  const [target, setTarget] = useState("충전기");
  const [cycle, setCycle] = useState("월간");
  const [type, setType] = useState("정기점검");
  const [siteName, setSiteName] = useState("서울숲 충전소"); // Default mock
  const [siteId, setSiteId] = useState("site-seoulforest");
  const [memo, setMemo] = useState("");
  const [checklist, setChecklist] = useState<ChecklistItem[]>([]);
  const [loadingPreset, setLoadingPreset] = useState(false);
  const [loadingDraft, setLoadingDraft] = useState(false);
  const [draft, setDraft] = useState<any | null>(null);
  const [saving, setSaving] = useState(false);
  const [saveSuccess, setSaveSuccess] = useState(false);

  // Feedback form state
  const [fbRole, setFbRole] = useState("엔지니어");
  const [fbRating, setFbRating] = useState(4);
  const [fbUsefulness, setFbUsefulness] = useState(4);
  const [fbComment, setFbComment] = useState("");
  const [fbSaved, setFbSaved] = useState(false);

  useEffect(() => {
    // Generate UUID-like inspection_id on client load
    setInspectionId(`ins-${Math.random().toString(36).substring(2, 8)}${Math.random().toString(36).substring(2, 8)}`);
  }, []);

  // Fetch checklist preset when target or cycle changes
  useEffect(() => {
    setLoadingPreset(true);
    fetch(`${getApiUrl()}/api/v1/inspection/preset?target=${encodeURIComponent(target)}&cycle=${encodeURIComponent(cycle)}`)
      .then((res) => res.json())
      .then((data) => {
        setChecklist(data.checklist);
        setLoadingPreset(false);
      })
      .catch((err) => {
        console.error("Failed to load preset:", err);
        setLoadingPreset(false);
      });
  }, [target, cycle]);

  const handleStatusChange = (idx: number, status: string) => {
    const nextList = [...checklist];
    nextList[idx].status = status;
    setChecklist(nextList);
  };

  const handleNoteChange = (idx: number, note: string) => {
    const nextList = [...checklist];
    nextList[idx].note = note;
    setChecklist(nextList);
  };

  const handleGenerateDraft = async () => {
    setLoadingDraft(true);
    try {
      const res = await fetch(`${getApiUrl()}/api/v1/inspection/draft`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          target,
          cycle,
          checklist,
          memo,
          tenant_id: getTenantId(),
        }),
      });
      if (!res.ok) {
        alert(await readApiError(res));
        return;
      }
      const data = await res.json();
      setDraft(data);
    } catch (err) {
      alert("AI 초안 생성에 실패했습니다.");
    } finally {
      setLoadingDraft(false);
    }
  };

  const handleSaveLog = async () => {
    setSaving(true);
    try {
      const res = await fetch(`${getApiUrl()}/api/v1/inspection/log`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          inspection_id: inspectionId,
          tenant_id: getTenantId(),
          site_id: siteId,
          inspection_cycle: cycle,
          inspection_type: type,
          checklist,
          memo_text: memo,
          ai_summary: draft ? JSON.stringify(draft.summary_json) : null,
        }),
      });
      if (res.ok) {
        setSaveSuccess(true);
        // Confirm the log immediately for MVP
        await fetch(`${getApiUrl()}/api/v1/inspection/logs/${inspectionId}/confirm`, {
          method: "POST",
        });
      } else {
        alert("점검일지 저장에 실패했습니다.");
      }
    } catch (err) {
      alert("점검일지 저장에 실패했습니다.");
    } finally {
      setSaving(false);
    }
  };

  const handleSaveFeedback = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      const res = await fetch(`${getApiUrl()}/api/v1/feedbacks`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          target_type: "draft",
          target_id: inspectionId,
          role: fbRole,
          rating: fbRating,
          usefulness: fbUsefulness,
          comment: fbComment,
        }),
      });
      if (res.ok) {
        setFbSaved(true);
      }
    } catch (err) {
      console.error(err);
    }
  };

  return (
    <div style={{ animation: "fadeIn 0.5s ease-out" }}>
      <header style={{ marginBottom: "36px" }}>
        <h2 style={{ fontSize: "28px", fontWeight: "bold", margin: "0 0 8px 0" }}>📝 점검일지 AI 어시스턴트</h2>
        <p style={{ color: "#94a3b8", margin: 0, fontSize: "14px" }}>
          현장 점검 정보를 기입하고 AI를 통해 위험도 판정 및 최종 보고서 초안을 자동으로 작성해 보세요.
        </p>
      </header>

      <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "24px" }}>
        
        {/* Left Side: Form and Checklist Editor */}
        <section className="glass-panel" style={{ padding: "32px" }}>
          <h3 style={{ fontSize: "18px", fontWeight: "bold", margin: "0 0 24px 0", color: "#f8fafc" }}>📋 점검 내역 입력</h3>

          <div style={{ display: "flex", gap: "16px", marginBottom: "20px" }}>
            <div style={{ flex: 1 }}>
              <label style={{ fontSize: "13px", color: "#94a3b8", display: "block", marginBottom: "6px" }}>점검대상</label>
              <select value={target} onChange={(e) => setTarget(e.target.value)} style={{ width: "100%", padding: "10px", background: "#1e293b", border: "1px solid rgba(255,255,255,0.08)", borderRadius: "8px", color: "#f8fafc" }}>
                <option value="충전기">충전기</option>
                <option value="커넥터">커넥터</option>
                <option value="케이블">케이블</option>
                <option value="수배전반">수배전반</option>
              </select>
            </div>
            <div style={{ flex: 1 }}>
              <label style={{ fontSize: "13px", color: "#94a3b8", display: "block", marginBottom: "6px" }}>점검주기</label>
              <select value={cycle} onChange={(e) => setCycle(e.target.value)} style={{ width: "100%", padding: "10px", background: "#1e293b", border: "1px solid rgba(255,255,255,0.08)", borderRadius: "8px", color: "#f8fafc" }}>
                <option value="월간">월간</option>
                <option value="주간">주간</option>
                <option value="일간">일간</option>
                <option value="수시">수시</option>
              </select>
            </div>
          </div>

          <div style={{ display: "flex", gap: "16px", marginBottom: "24px" }}>
            <div style={{ flex: 1 }}>
              <label style={{ fontSize: "13px", color: "#94a3b8", display: "block", marginBottom: "6px" }}>점검현장</label>
              <input type="text" value={siteName} onChange={(e) => setSiteName(e.target.value)} style={{ width: "100%", padding: "10px", background: "#1e293b", border: "1px solid rgba(255,255,255,0.08)", borderRadius: "8px", color: "#f8fafc" }} />
            </div>
            <div style={{ flex: 1 }}>
              <label style={{ fontSize: "13px", color: "#94a3b8", display: "block", marginBottom: "6px" }}>점검유형</label>
              <select value={type} onChange={(e) => setType(e.target.value)} style={{ width: "100%", padding: "10px", background: "#1e293b", border: "1px solid rgba(255,255,255,0.08)", borderRadius: "8px", color: "#f8fafc" }}>
                <option value="정기점검">정기점검</option>
                <option value="설치후점검">설치후점검</option>
                <option value="고장 AS">고장 AS</option>
                <option value="긴급출동">긴급출동</option>
              </select>
            </div>
          </div>

          {/* Checklist Area */}
          <div style={{ marginBottom: "24px" }}>
            <h4 style={{ fontSize: "15px", fontWeight: "bold", margin: "0 0 12px 0" }}>점검 항목 상태 수정</h4>
            
            {loadingPreset ? (
              <div style={{ color: "#94a3b8", fontSize: "14px" }}>프리셋을 불러오는 중...</div>
            ) : (
              <div style={{ display: "flex", flexDirection: "column", gap: "12px" }}>
                {checklist.map((item, idx) => (
                  <div key={idx} style={{ display: "flex", gap: "12px", alignItems: "center", background: "rgba(255,255,255,0.02)", padding: "12px", borderRadius: "8px", border: "1px solid rgba(255,255,255,0.04)" }}>
                    <div style={{ flex: 2, fontSize: "14px", color: "#f8fafc" }}>{item.item}</div>
                    
                    <select value={item.status} onChange={(e) => handleStatusChange(idx, e.target.value)} style={{ flex: 1, padding: "6px", background: "#0f172a", border: "1px solid rgba(255,255,255,0.08)", borderRadius: "6px", color: "#f8fafc", fontSize: "13px" }}>
                      <option value="정상">정상</option>
                      <option value="주의">주의</option>
                      <option value="이상">이상</option>
                      <option value="N/A">N/A</option>
                    </select>

                    <input type="text" placeholder="특이사항 적기" value={item.note} onChange={(e) => handleNoteChange(idx, e.target.value)} style={{ flex: 2, padding: "6px", background: "#0f172a", border: "1px solid rgba(255,255,255,0.08)", borderRadius: "6px", color: "#f8fafc", fontSize: "13px" }} />
                  </div>
                ))}
              </div>
            )}
          </div>

          {/* General Memo */}
          <div style={{ marginBottom: "24px" }}>
            <label style={{ fontSize: "13px", color: "#94a3b8", display: "block", marginBottom: "6px" }}>추가 전달/특이 메모</label>
            <textarea placeholder="점검 현장 특이사항이 있다면 기록해 주세요." value={memo} onChange={(e) => setMemo(e.target.value)} style={{ width: "100%", height: "100px", padding: "12px", background: "#1e293b", border: "1px solid rgba(255,255,255,0.08)", borderRadius: "8px", color: "#f8fafc", fontSize: "14px" }} />
          </div>

          <button onClick={handleGenerateDraft} disabled={loadingDraft || checklist.length === 0} style={{ width: "100%", padding: "14px", background: "#06b6d4", color: "#ffffff", border: "none", borderRadius: "8px", fontWeight: "bold", cursor: "pointer", transition: "background 0.2s" }}>
            {loadingDraft ? "AI 분석 및 초안 생성 중..." : "⚡ AI 초안 생성"}
          </button>
        </section>

        {/* Right Side: AI Draft Results */}
        <section style={{ display: "flex", flexDirection: "column", gap: "24px" }}>
          
          <div className="glass-panel" style={{ padding: "32px", flex: 1, display: "flex", flexDirection: "column" }}>
            <h3 style={{ fontSize: "18px", fontWeight: "bold", margin: "0 0 20px 0", color: "#f8fafc" }}>💡 AI 점검 결과 분석 초안</h3>
            
            {!draft ? (
              <div style={{ flex: 1, display: "flex", justifyContent: "center", alignItems: "center", color: "#64748b", border: "2px dashed rgba(255,255,255,0.04)", borderRadius: "12px", padding: "40px", textAlign: "center" }}>
                좌측 폼을 작성하고 'AI 초안 생성' 버튼을 클릭하시면 실시간 AI 요약 및 정비 가이드 초안이 렌더링됩니다.
              </div>
            ) : (
              <div style={{ display: "flex", flexDirection: "column", gap: "20px", flex: 1 }}>
                
                {/* Risk and Summary Card */}
                <div style={{ background: "rgba(255,255,255,0.03)", padding: "20px", borderRadius: "10px", border: "1px solid rgba(255,255,255,0.06)" }}>
                  <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "12px" }}>
                    <span style={{ fontSize: "14px", color: "#94a3b8" }}>AI 위험도 판정</span>
                    <span style={{
                      padding: "4px 10px",
                      borderRadius: "6px",
                      fontSize: "13px",
                      fontWeight: "bold",
                      background: draft.summary_json?.overall_risk === "high" ? "rgba(239, 68, 68, 0.2)" : draft.summary_json?.overall_risk === "mid" ? "rgba(245, 158, 11, 0.2)" : "rgba(16, 185, 129, 0.2)",
                      color: draft.summary_json?.overall_risk === "high" ? "#ef4444" : draft.summary_json?.overall_risk === "mid" ? "#f59e0b" : "#10b981"
                    }}>
                      {draft.summary_json?.overall_risk ? draft.summary_json.overall_risk.toUpperCase() : "LOW"}
                    </span>
                  </div>
                  <h4 style={{ fontSize: "16px", fontWeight: "bold", margin: "0 0 8px 0" }}>요약 가이드</h4>
                  <p style={{ margin: 0, fontSize: "14px", color: "#cbd5e1", lineHeight: "1.6" }}>
                    {draft.draft_text}
                  </p>
                </div>

                {/* Structured JSON display */}
                {draft.summary_json && (
                  <div>
                    <h4 style={{ fontSize: "15px", fontWeight: "bold", margin: "0 0 10px 0" }}>권장 현장 대처 조치</h4>
                    <ul style={{ paddingLeft: "20px", margin: 0, fontSize: "13px", color: "#94a3b8", display: "flex", flexDirection: "column", gap: "6px" }}>
                      {draft.summary_json.recommended_actions?.map((act: string, idx: number) => (
                        <li key={idx} style={{ color: "#cbd5e1" }}>{act}</li>
                      ))}
                    </ul>
                  </div>
                )}

                {/* Save Block */}
                {saveSuccess ? (
                  <div style={{ background: "rgba(16, 185, 129, 0.1)", border: "1px solid #10b981", borderRadius: "8px", padding: "16px", color: "#10b981", fontWeight: "bold", textAlign: "center" }}>
                    ✓ 점검일지가 서버 데이터베이스에 안전하게 저장 및 확정되었습니다.
                  </div>
                ) : (
                  <button onClick={handleSaveLog} disabled={saving} style={{ width: "100%", padding: "14px", background: "#10b981", color: "#ffffff", border: "none", borderRadius: "8px", fontWeight: "bold", cursor: "pointer", marginTop: "auto" }}>
                    {saving ? "저장 중..." : "점검일지 최종 확정 및 저장"}
                  </button>
                )}
              </div>
            )}
          </div>

          {/* Feedback Form (Visible after Draft generation) */}
          {draft && !fbSaved && (
            <div className="glass-panel" style={{ padding: "24px" }}>
              <h4 style={{ fontSize: "14px", fontWeight: "bold", margin: "0 0 12px 0", color: "#f8fafc" }}>이 요약 초안에 대한 피드백 남기기</h4>
              <form onSubmit={handleSaveFeedback} style={{ display: "flex", flexDirection: "column", gap: "10px" }}>
                <div style={{ display: "flex", gap: "12px" }}>
                  <select value={fbRole} onChange={(e) => setFbRole(e.target.value)} style={{ flex: 1, padding: "8px", background: "#1e293b", border: "1px solid rgba(255,255,255,0.08)", borderRadius: "6px", color: "#f8fafc", fontSize: "13px" }}>
                    <option value="엔지니어">엔지니어</option>
                    <option value="운영자">운영자</option>
                    <option value="고객사">고객사</option>
                  </select>
                  <div style={{ flex: 2, display: "flex", alignItems: "center", gap: "8px", fontSize: "12px", color: "#94a3b8" }}>
                    만족도:
                    <input type="range" min="1" max="5" value={fbRating} onChange={(e) => setFbRating(Number(e.target.value))} style={{ flex: 1 }} />
                    {fbRating}점
                  </div>
                </div>
                <textarea placeholder="개선 사항이 있다면 제안해주세요." value={fbComment} onChange={(e) => setFbComment(e.target.value)} style={{ width: "100%", height: "60px", padding: "8px", background: "#1e293b", border: "1px solid rgba(255,255,255,0.08)", borderRadius: "6px", color: "#f8fafc", fontSize: "13px" }} />
                <button type="submit" style={{ padding: "8px", background: "#3b82f6", color: "#ffffff", border: "none", borderRadius: "6px", fontSize: "13px", fontWeight: "bold", cursor: "pointer" }}>피드백 제출</button>
              </form>
            </div>
          )}
          
          {fbSaved && (
            <div className="glass-panel" style={{ padding: "16px", color: "#10b981", textAlign: "center", fontSize: "13px", fontWeight: "bold" }}>
              ✓ 피드백이 성공적으로 등록되었습니다. 감사합니다!
            </div>
          )}
        </section>
      </div>
    </div>
  );
}
