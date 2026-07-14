"use client";

import React, { useState } from "react";
import { getApiUrl, getTenantId, readApiError } from "../utils";
import AiUsageBadge from "../components/AiUsageBadge";

export default function SearchPage() {
  const [query, setQuery] = useState("");
  const [useWebSearch, setUseWebSearch] = useState(false);
  const [kHybrid, setKHybrid] = useState(30);
  const [kDense, setKDense] = useState(50);
  const [kSparse, setKSparse] = useState(50);
  
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<any | null>(null);

  // Feedback form state
  const [fbRole, setFbRole] = useState("엔지니어");
  const [fbRating, setFbRating] = useState(4);
  const [fbUsefulness, setFbUsefulness] = useState(4);
  const [fbComment, setFbComment] = useState("");
  const [fbSaved, setFbSaved] = useState(false);

  const handleSearch = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!query.trim()) return;

    setLoading(true);
    setResult(null);
    setFbSaved(false);

    try {
      const res = await fetch(`${getApiUrl()}/api/v1/search/as-cases`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          query: query.trim(),
          tenant_id: getTenantId(),
          use_web_search: useWebSearch,
          k_hybrid: kHybrid,
          k_dense: kDense,
          k_sparse: kSparse,
        }),
      });
      if (!res.ok) throw new Error(await readApiError(res));
      const data = await res.json();
      setResult(data);
    } catch (err) {
      alert(err instanceof Error ? err.message : "검색 도중 에러가 발생했습니다.");
    } finally {
      setLoading(false);
    }
  };

  const handleSaveFeedback = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      const res = await fetch(`${getApiUrl()}/api/v1/feedbacks`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          target_type: "search",
          target_id: query.trim().substring(0, 80),
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
        <h2 style={{ fontSize: "28px", fontWeight: "bold", margin: "0 0 8px 0" }}>🔎 AS 유사 사례 검색</h2>
        <p style={{ color: "#94a3b8", margin: 0, fontSize: "14px" }}>
          장애 코드나 고장 현상을 자유롭게 작성하면 하이브리드 RAG로 정교한 조치 가이드를 제공합니다.
        </p>
      </header>

      {/* Search Input Box */}
      <section className="glass-panel" style={{ padding: "32px", marginBottom: "24px" }}>
        <form onSubmit={handleSearch}>
          <textarea
            placeholder="증상·에러·현상을 입력하세요 (예: 에러코드 23, RFID 인식 안 됨, PLC 하트비트 없음)"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            style={{
              width: "100%",
              height: "120px",
              padding: "16px",
              background: "#1e293b",
              border: "1px solid rgba(255,255,255,0.08)",
              borderRadius: "8px",
              color: "#f8fafc",
              fontSize: "14px",
              marginBottom: "16px",
              outline: "none",
              resize: "none",
            }}
          />

          <div style={{ display: "flex", gap: "24px", alignItems: "center", marginBottom: "20px", flexWrap: "wrap" }}>
            <label style={{ display: "flex", alignItems: "center", gap: "8px", fontSize: "14px", cursor: "pointer", color: "#cbd5e1" }}>
              <input type="checkbox" checked={useWebSearch} onChange={(e) => setUseWebSearch(e.target.checked)} style={{ width: "16px", height: "16px" }} />
              🌐 웹 리서치 포함 (Tavily 연동)
            </label>
          </div>

          {/* Advanced Sliders */}
          <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(200px, 1fr))", gap: "20px", marginBottom: "24px", padding: "16px", background: "rgba(255,255,255,0.02)", borderRadius: "8px" }}>
            <div>
              <div style={{ display: "flex", justifyContent: "space-between", fontSize: "12px", color: "#94a3b8", marginBottom: "6px" }}>
                <span>1차 하이브리드 후보 수</span>
                <span>{kHybrid}개</span>
              </div>
              <input type="range" min="15" max="50" value={kHybrid} onChange={(e) => setKHybrid(Number(e.target.value))} style={{ width: "100%" }} />
            </div>
            <div>
              <div style={{ display: "flex", justifyContent: "space-between", fontSize: "12px", color: "#94a3b8", marginBottom: "6px" }}>
                <span>Dense(벡터) 상한</span>
                <span>{kDense}개</span>
              </div>
              <input type="range" min="20" max="80" value={kDense} onChange={(e) => setKDense(Number(e.target.value))} style={{ width: "100%" }} />
            </div>
            <div>
              <div style={{ display: "flex", justifyContent: "space-between", fontSize: "12px", color: "#94a3b8", marginBottom: "6px" }}>
                <span>Sparse(BM25) 상한</span>
                <span>{kSparse}개</span>
              </div>
              <input type="range" min="20" max="80" value={kSparse} onChange={(e) => setKSparse(Number(e.target.value))} style={{ width: "100%" }} />
            </div>
          </div>

          <button type="submit" disabled={loading || !query.trim()} style={{ width: "100%", padding: "14px", background: "#06b6d4", color: "#ffffff", border: "none", borderRadius: "8px", fontWeight: "bold", cursor: "pointer", fontSize: "15px" }}>
            {loading ? "RAG 지식 검색 및 생성 중..." : "유사 사례 검색 및 답변"}
          </button>
        </form>
      </section>

      {/* Loading Indicator */}
      {loading && (
        <div style={{ display: "flex", justifyContent: "center", padding: "40px" }}>
          <div className="spinner" style={{ border: "4px solid rgba(255,255,255,0.1)", borderTop: "4px solid #06b6d4", borderRadius: "50%", width: "40px", height: "40px", animation: "spin 1s linear infinite" }} />
        </div>
      )}

      {/* Result Section */}
      {result && (
        <div style={{ display: "flex", flexDirection: "column", gap: "24px", animation: "fadeIn 0.4s" }}>
          
          {/* Status banners — embedding(RAG) vs LLM are separate */}
          {result.embedding_degraded && (
            <div style={{ background: "rgba(245, 158, 11, 0.1)", border: "1px solid #f59e0b", borderRadius: "8px", padding: "16px", color: "#f59e0b", fontSize: "14px" }}>
              ⚠️ <strong>벡터 검색(RAG)</strong>은 서버 OpenAI Embedding 할당량 초과로 BM25 키워드 검색만 사용 중입니다.
              Groq는 답변 생성용이며 임베딩 검색을 대체하지 않습니다.
            </div>
          )}
          {result.llm_error && (
            <div style={{ background: "rgba(239, 68, 68, 0.1)", border: "1px solid #ef4444", borderRadius: "8px", padding: "16px", color: "#fca5a5", fontSize: "14px" }}>
              ⚠️ AI 답변 생성 실패 — AI 설정에서 <strong>Groq API 키</strong> 저장 및 연결 테스트를 확인해 주세요.
              (Gemini 무료 tier quota 0이면 Groq 1순위 사용 권장)
            </div>
          )}
          {(result.ai_usage || result.llm_model) && (
            <AiUsageBadge usage={result.ai_usage} fallbackModel={result.llm_model || (result.llm_error ? "offline-rules" : null)} />
          )}

          {/* Metrics */}
          <div style={{ display: "grid", gridTemplateColumns: "repeat(3, 1fr)", gap: "16px" }}>
            <div className="glass-panel" style={{ padding: "16px", textAlign: "center" }}>
              <div style={{ fontSize: "11px", color: "#94a3b8" }}>신뢰도 점수</div>
              <div style={{ fontSize: "20px", fontWeight: "bold", marginTop: "4px", color: "#06b6d4" }}>{result.confidence.toFixed(3)}</div>
            </div>
            <div className="glass-panel" style={{ padding: "16px", textAlign: "center" }}>
              <div style={{ fontSize: "11px", color: "#94a3b8" }}>신뢰 등급</div>
              <div style={{ fontSize: "20px", fontWeight: "bold", marginTop: "4px", color: result.level === "high" ? "#10b981" : result.level === "mid" ? "#f59e0b" : "#ef4444" }}>
                {result.level.toUpperCase()}
              </div>
            </div>
            <div className="glass-panel" style={{ padding: "16px", textAlign: "center" }}>
              <div style={{ fontSize: "11px", color: "#94a3b8" }}>매칭 후보수</div>
              <div style={{ fontSize: "20px", fontWeight: "bold", marginTop: "4px", color: "#cbd5e1" }}>{result.candidate_count}개</div>
            </div>
          </div>

          {/* Answer Card */}
          <section className="glass-panel" style={{ padding: "32px" }}>
            <h3 style={{ fontSize: "18px", fontWeight: "bold", margin: "0 0 20px 0" }}>구조화 답변</h3>
            
            <div style={{ display: "flex", flexDirection: "column", gap: "20px" }}>
              <div>
                <span style={{ fontSize: "12px", color: "#94a3b8", display: "block", marginBottom: "4px" }}>증상 요약</span>
                <span style={{ fontSize: "15px", color: "#f8fafc", fontWeight: "bold" }}>{result.structured.symptom_summary}</span>
              </div>

              {result.structured.top_causes?.length > 0 && (
                <div>
                  <span style={{ fontSize: "12px", color: "#94a3b8", display: "block", marginBottom: "6px" }}>가능 원인 (최대 3)</span>
                  <ol style={{ margin: 0, paddingLeft: "20px", fontSize: "14px", color: "#cbd5e1", display: "flex", flexDirection: "column", gap: "4px" }}>
                    {result.structured.top_causes.map((c: string, idx: number) => (
                      <li key={idx}>{c}</li>
                    ))}
                  </ol>
                </div>
              )}

              {result.structured.inspection_steps?.length > 0 && (
                <div>
                  <span style={{ fontSize: "12px", color: "#94a3b8", display: "block", marginBottom: "6px" }}>점검 순서</span>
                  <ol style={{ margin: 0, paddingLeft: "20px", fontSize: "14px", color: "#cbd5e1", display: "flex", flexDirection: "column", gap: "4px" }}>
                    {result.structured.inspection_steps.map((s: string, idx: number) => (
                      <li key={idx}>{s}</li>
                    ))}
                  </ol>
                </div>
              )}

              <div>
                <span style={{ fontSize: "12px", color: "#94a3b8", display: "block", marginBottom: "4px" }}>교체 부품</span>
                <span style={{ fontSize: "14px", color: "#cbd5e1" }}>{result.structured.parts}</span>
              </div>

              {result.structured.evidence_refs?.length > 0 && (
                <div>
                  <span style={{ fontSize: "12px", color: "#94a3b8", display: "block", marginBottom: "6px" }}>근거 출처</span>
                  <ul style={{ margin: 0, paddingLeft: "20px", fontSize: "13px", color: "#94a3b8", display: "flex", flexDirection: "column", gap: "4px" }}>
                    {result.structured.evidence_refs.map((e: string, idx: number) => (
                      <li key={idx}><code>{e}</code></li>
                    ))}
                  </ul>
                </div>
              )}

              <div style={{ background: "rgba(6, 182, 212, 0.05)", border: "1px solid rgba(6, 182, 212, 0.15)", padding: "16px", borderRadius: "8px", fontSize: "13px", color: "#06b6d4", lineHeight: "1.6" }}>
                ℹ️ {result.structured.confidence_note}
              </div>
            </div>
          </section>

          {/* Source Docs Accordion */}
          <section className="glass-panel" style={{ padding: "24px" }}>
            <details>
              <summary style={{ cursor: "pointer", fontWeight: "bold", fontSize: "15px", color: "#cbd5e1", outline: "none" }}>
                🔎 검색·재순위에 사용된 상위 청크 (로컬 DB 원문 보기)
              </summary>
              <div style={{ marginTop: "20px", display: "flex", flexDirection: "column", gap: "16px" }}>
                {result.metadata_docs?.map((d: any, idx: number) => (
                  <div key={idx} style={{ background: "rgba(255,255,255,0.02)", padding: "16px", borderRadius: "8px", border: "1px solid rgba(255,255,255,0.04)", fontSize: "13px" }}>
                    <div style={{ display: "flex", justifyContent: "space-between", color: "#64748b", marginBottom: "8px", fontSize: "11px", fontFamily: "monospace" }}>
                      <span>#{idx + 1} | {d.metadata.source}</span>
                      <span>Row {d.metadata.row}</span>
                    </div>
                    <pre style={{ margin: 0, whiteSpace: "pre-wrap", wordBreak: "break-all", fontFamily: "sans-serif", color: "#94a3b8", lineHeight: "1.5" }}>
                      {d.page_content}
                    </pre>
                  </div>
                ))}
              </div>
            </details>
          </section>

          {/* Feedback Form */}
          {!fbSaved && (
            <section className="glass-panel" style={{ padding: "32px" }}>
              <h3 style={{ fontSize: "16px", fontWeight: "bold", margin: "0 0 16px 0" }}>📬 검색 결과 만족도 피드백 남기기</h3>
              <form onSubmit={handleSaveFeedback} style={{ display: "flex", flexDirection: "column", gap: "16px" }}>
                <div style={{ display: "flex", gap: "24px", flexWrap: "wrap" }}>
                  <div style={{ flex: 1, minWidth: "150px" }}>
                    <label style={{ fontSize: "12px", color: "#94a3b8", display: "block", marginBottom: "6px" }}>역할</label>
                    <select value={fbRole} onChange={(e) => setFbRole(e.target.value)} style={{ width: "100%", padding: "10px", background: "#1e293b", border: "1px solid rgba(255,255,255,0.08)", borderRadius: "8px", color: "#f8fafc", fontSize: "13px" }}>
                      <option value="엔지니어">엔지니어</option>
                      <option value="운영자">운영자</option>
                      <option value="고객사">고객사</option>
                    </select>
                  </div>
                  <div style={{ flex: 1, minWidth: "150px" }}>
                    <label style={{ fontSize: "12px", color: "#94a3b8", display: "block", marginBottom: "6px" }}>전반 만족도</label>
                    <input type="range" min="1" max="5" value={fbRating} onChange={(e) => setFbRating(Number(e.target.value))} style={{ width: "100%" }} />
                    <span style={{ fontSize: "12px", color: "#cbd5e1" }}>⭐ {fbRating}점</span>
                  </div>
                  <div style={{ flex: 1, minWidth: "150px" }}>
                    <label style={{ fontSize: "12px", color: "#94a3b8", display: "block", marginBottom: "6px" }}>업무 도움도</label>
                    <input type="range" min="1" max="5" value={fbUsefulness} onChange={(e) => setFbUsefulness(Number(e.target.value))} style={{ width: "100%" }} />
                    <span style={{ fontSize: "12px", color: "#cbd5e1" }}>💡 {fbUsefulness}점</span>
                  </div>
                </div>
                <div>
                  <label style={{ fontSize: "12px", color: "#94a3b8", display: "block", marginBottom: "6px" }}>의견 / 개선 제안</label>
                  <textarea value={fbComment} onChange={(e) => setFbComment(e.target.value)} style={{ width: "100%", height: "80px", padding: "12px", background: "#1e293b", border: "1px solid rgba(255,255,255,0.08)", borderRadius: "8px", color: "#f8fafc", fontSize: "13px", outline: "none", resize: "none" }} />
                </div>
                <button type="submit" style={{ padding: "12px", background: "#3b82f6", color: "#ffffff", border: "none", borderRadius: "8px", fontWeight: "bold", cursor: "pointer", fontSize: "14px" }}>
                  피드백 제출
                </button>
              </form>
            </section>
          )}

          {fbSaved && (
            <div className="glass-panel" style={{ padding: "24px", color: "#10b981", textAlign: "center", fontWeight: "bold" }}>
              ✓ 피드백이 등록되었습니다. 소중한 의견 감사합니다!
            </div>
          )}
        </div>
      )}
    </div>
  );
}
