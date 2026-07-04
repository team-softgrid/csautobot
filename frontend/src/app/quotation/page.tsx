"use client";

import React, { useState, useEffect } from "react";
import { getApiUrl, getTenantId, readApiError } from "../utils";

interface PartItem {
  part_name: string;
  spec: string;
  qty: number;
  unit_price: number;
  category: string;
}

interface QuotationDraft {
  symptom_summary: string;
  likely_cause: string;
  parts: PartItem[];
  dispatch_fee: number;
  labor_fee: number;
}

export default function QuotationPage() {
  const [query, setQuery] = useState("");
  const [chargerType, setChargerType] = useState("급속");
  const [loading, setLoading] = useState(false);
  const [draft, setDraft] = useState<QuotationDraft | null>(null);

  // Manual part input states
  const [newPartName, setNewPartName] = useState("");
  const [newPartCat, setNewPartCat] = useState("급속");
  const [newPartQty, setNewPartQty] = useState(1);

  // API key fallback indicator
  const [openaiError, setOpenaiError] = useState(false);

  const handleCreateDraft = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!query.trim()) return;

    setLoading(true);
    setDraft(null);

    try {
      const res = await fetch(`${getApiUrl()}/api/v1/quotation/draft`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          query: query.trim(),
          charger_type: chargerType,
          tenant_id: getTenantId(),
        }),
      });

      if (!res.ok) {
        throw new Error(await readApiError(res));
      }
      const data = await res.json();
      
      setDraft({
        symptom_summary: data.symptom_summary,
        likely_cause: data.likely_cause,
        parts: data.parts,
        dispatch_fee: data.dispatch_fee,
        labor_fee: data.labor_fee
      });
      
      // If the backend had to fallback, it might set a flag or we can check errors
      setOpenaiError(data.openai_error || false);
    } catch (err) {
      alert(err instanceof Error ? err.message : "견적 산출 도중 에러가 발생했습니다.");
    } finally {
      setLoading(false);
    }
  };

  // Helper to lookup part price from backend/local rules via api or mock logic
  // We can fetch or simply match on client side based on our pricing table
  const handleAddPart = (e: React.FormEvent) => {
    e.preventDefault();
    if (!newPartName.trim() || !draft) return;

    // Direct lookup simulation matching backend services
    let contractPrice = 0;
    let spec = "수동 입력 품목";
    const nameClean = newPartName.trim().toLowerCase().replace(/\s+/g, "");

    const pricingList = [
      { name: "AC미터", spec: "OMWH-320D-B(좌타입)", price: 130000 },
      { name: "DC미터 전력량계", spec: "1P2W 1000V 200A", price: 185000 },
      { name: "IC결제만달기", spec: "IC/RF/MS(SVM600)", price: 385000 },
      { name: "LCD", spec: "8인치 액정 패널", price: 120000 },
      { name: "PLC 모뎀", spec: "PEPPERMINT-NNA_000(신형)", price: 500000 },
      { name: "RFID리더기", spec: "ATM-100", price: 94000 },
      { name: "누전차단기", spec: "ELCB 4P 100A TYPE (감도 30/50/100mA)", price: 260000 },
      { name: "보드", spec: "EV Charger Controller V2.1", price: 500000 },
      { name: "보드", spec: "MDI-UC-1 V2.0 (8인치보드)", price: 525000 },
      { name: "보드", spec: "MDI-UC1-PILOT V4.0", price: 110000 },
      { name: "산업용 PC", spec: "12.1인치(신형)", price: 1248000 },
      { name: "충전케이블", spec: "SW-EVT201MD-006 (CCS1/200A)", price: 1050000 },
      { name: "충전케이블", spec: "AC 5핀 32A 5M 완속", price: 120000 },
      { name: "파워모듈", spec: "REG1K0100G (30KW)", price: 1800000 },
      { name: "파워모듈", spec: "REG50040 (15KW)", price: 1200000 },
    ];

    const match = pricingList.find(p => nameClean.includes(p.name.toLowerCase().replace(/\s+/g, "")));
    if (match) {
      contractPrice = match.price;
      spec = match.spec;
    }

    const updatedParts = [...draft.parts, {
      part_name: match ? match.name : newPartName.trim(),
      spec: spec,
      qty: newPartQty,
      unit_price: contractPrice,
      category: newPartCat
    }];

    setDraft({ ...draft, parts: updatedParts });
    setNewPartName("");
    setNewPartQty(1);
  };

  const handleUpdateQty = (index: number, newQty: number) => {
    if (!draft) return;
    const updatedParts = draft.parts.map((p, idx) => 
      idx === index ? { ...p, qty: Math.max(1, newQty) } : p
    );
    setDraft({ ...draft, parts: updatedParts });
  };

  const handleDeletePart = (index: number) => {
    if (!draft) return;
    const updatedParts = draft.parts.filter((_, idx) => idx !== index);
    setDraft({ ...draft, parts: updatedParts });
  };

  const handleUpdateFee = (type: "dispatch" | "labor", value: number) => {
    if (!draft) return;
    if (type === "dispatch") {
      setDraft({ ...draft, dispatch_fee: Math.max(0, value) });
    } else {
      setDraft({ ...draft, labor_fee: Math.max(0, value) });
    }
  };

  // Calculations
  const partsTotal = draft ? draft.parts.reduce((sum, p) => sum + (p.unit_price * p.qty), 0) : 0;
  const dispatchFee = draft ? draft.dispatch_fee : 0;
  const laborFee = draft ? draft.labor_fee : 0;
  const supplyValue = partsTotal + dispatchFee + laborFee;
  const vat = Math.floor(supplyValue * 0.1);
  const grandTotal = supplyValue + vat;

  // Excel Generator and Downloader (Server-side)
  const handleDownloadExcel = async () => {
    if (!draft) return;

    try {
      const res = await fetch(`${getApiUrl()}/api/v1/quotation/export`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          query: query.trim(),
          symptom_summary: draft.symptom_summary,
          likely_cause: draft.likely_cause,
          parts: draft.parts.map(p => ({
            part_name: p.part_name,
            spec: p.spec,
            qty: p.qty,
            unit_price: p.unit_price,
            category: p.category
          })),
          dispatch_fee: draft.dispatch_fee,
          labor_fee: draft.labor_fee
        }),
      });

      if (!res.ok) throw new Error("엑셀 파일 생성 요청에 실패했습니다.");
      
      const blob = await res.blob();
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement("a");
      link.href = url;
      
      const filenameSymptom = query.substring(0, 10).replace(/\s+/g, "_");
      link.setAttribute("download", `견적서_${filenameSymptom}.xlsx`);
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      window.URL.revokeObjectURL(url);
    } catch (err) {
      alert(err instanceof Error ? err.message : "엑셀 다운로드 도중 에러가 발생했습니다.");
    }
  };

  return (
    <div style={{ animation: "fadeIn 0.5s ease-out" }}>
      <header style={{ marginBottom: "36px" }}>
        <h2 style={{ fontSize: "28px", fontWeight: "bold", margin: "0 0 8px 0" }}>💡 AI 견적서 생성기</h2>
        <p style={{ color: "#94a3b8", margin: 0, fontSize: "14px" }}>
          고장 접수 내용을 분석하여 필요한 교체 부품과 계약 단가를 자동으로 조회해 견적서를 작성합니다.
        </p>
      </header>

      <div style={{ display: "grid", gridTemplateColumns: "1fr 1.5fr", gap: "28px", alignItems: "start" }}>
        {/* Left Column: Diagnostics Form */}
        <div>
          <section className="glass-panel" style={{ padding: "28px", marginBottom: "24px" }}>
            <h3 style={{ fontSize: "18px", fontWeight: "bold", marginBottom: "20px", color: "#f8fafc" }}>🔧 고장 진단 및 조건 설정</h3>
            <form onSubmit={handleCreateDraft}>
              <div style={{ marginBottom: "20px" }}>
                <label style={{ fontSize: "13px", color: "#94a3b8", display: "block", marginBottom: "8px" }}>
                  고객 접수 증상 및 불량 현상 입력
                </label>
                <textarea
                  placeholder="예: 급속 충전기 케이블 꽂자마자 충전 완료 뜸 / 카드 태깅 불량"
                  value={query}
                  onChange={(e) => setQuery(e.target.value)}
                  style={{
                    width: "100%",
                    height: "120px",
                    padding: "12px",
                    background: "#1e293b",
                    border: "1px solid rgba(255,255,255,0.08)",
                    borderRadius: "6px",
                    color: "#f8fafc",
                    fontSize: "14px",
                    outline: "none",
                    resize: "none"
                  }}
                  required
                />
              </div>

              <div style={{ marginBottom: "24px" }}>
                <label style={{ fontSize: "13px", color: "#94a3b8", display: "block", marginBottom: "8px" }}>
                  충전기 구분
                </label>
                <select
                  value={chargerType}
                  onChange={(e) => setChargerType(e.target.value)}
                  style={{
                    width: "100%",
                    padding: "10px",
                    background: "#1e293b",
                    border: "1px solid rgba(255,255,255,0.08)",
                    borderRadius: "6px",
                    color: "#f8fafc",
                    fontSize: "14px",
                    outline: "none"
                  }}
                >
                  <option value="급속">급속 충전기</option>
                  <option value="완속">완속 충전기</option>
                </select>
              </div>

              <button
                type="submit"
                disabled={loading || !query.trim()}
                style={{
                  width: "100%",
                  padding: "14px",
                  background: "#06b6d4",
                  color: "#ffffff",
                  border: "none",
                  borderRadius: "6px",
                  fontWeight: "bold",
                  cursor: "pointer",
                  fontSize: "15px",
                  transition: "all 0.2s"
                }}
              >
                {loading ? "AS 사례 분석 및 견적 매핑 중..." : "✨ AI 견적서 초안 생성"}
              </button>
            </form>
          </section>

          {/* Manual Part Add Form (Only visible when draft exists) */}
          {draft && (
            <section className="glass-panel" style={{ padding: "24px" }}>
              <h3 style={{ fontSize: "16px", fontWeight: "bold", marginBottom: "16px", color: "#f8fafc" }}>➕ 수동 부품 추가</h3>
              <form onSubmit={handleAddPart}>
                <div style={{ display: "grid", gridTemplateColumns: "2fr 1fr 1fr", gap: "12px", alignItems: "end" }}>
                  <div>
                    <label style={{ fontSize: "11px", color: "#94a3b8", display: "block", marginBottom: "4px" }}>부품명</label>
                    <input
                      type="text"
                      placeholder="예: LCD 패널"
                      value={newPartName}
                      onChange={(e) => setNewPartName(e.target.value)}
                      style={{
                        width: "100%",
                        padding: "8px",
                        background: "#1e293b",
                        border: "1px solid rgba(255,255,255,0.08)",
                        borderRadius: "6px",
                        color: "#f8fafc",
                        fontSize: "13px",
                        outline: "none"
                      }}
                      required
                    />
                  </div>
                  <div>
                    <label style={{ fontSize: "11px", color: "#94a3b8", display: "block", marginBottom: "4px" }}>구분</label>
                    <select
                      value={newPartCat}
                      onChange={(e) => setNewPartCat(e.target.value)}
                      style={{
                        width: "100%",
                        padding: "8px",
                        background: "#1e293b",
                        border: "1px solid rgba(255,255,255,0.08)",
                        borderRadius: "6px",
                        color: "#f8fafc",
                        fontSize: "13px",
                        outline: "none"
                      }}
                    >
                      <option value="급속">급속</option>
                      <option value="완속">완속</option>
                      <option value="공용">공용</option>
                    </select>
                  </div>
                  <div>
                    <label style={{ fontSize: "11px", color: "#94a3b8", display: "block", marginBottom: "4px" }}>수량</label>
                    <input
                      type="number"
                      min="1"
                      value={newPartQty}
                      onChange={(e) => setNewPartQty(Number(e.target.value))}
                      style={{
                        width: "100%",
                        padding: "8px",
                        background: "#1e293b",
                        border: "1px solid rgba(255,255,255,0.08)",
                        borderRadius: "6px",
                        color: "#f8fafc",
                        fontSize: "13px",
                        outline: "none"
                      }}
                    />
                  </div>
                </div>
                <button
                  type="submit"
                  style={{
                    width: "100%",
                    marginTop: "16px",
                    padding: "10px",
                    background: "transparent",
                    color: "#06b6d4",
                    border: "1px solid #06b6d4",
                    borderRadius: "6px",
                    fontWeight: "bold",
                    cursor: "pointer",
                    fontSize: "13px",
                    transition: "all 0.2s"
                  }}
                  onMouseEnter={(e) => { e.currentTarget.style.background = "rgba(6,182,212,0.1)"; }}
                  onMouseLeave={(e) => { e.currentTarget.style.background = "transparent"; }}
                >
                  부품 추가
                </button>
              </form>
            </section>
          )}
        </div>

        {/* Right Column: Output Quotation Display */}
        <div>
          {loading && (
            <div style={{ display: "flex", justifyContent: "center", padding: "80px 0" }}>
              <div className="spinner" style={{ border: "4px solid rgba(255,255,255,0.1)", borderTop: "4px solid #06b6d4", borderRadius: "50%", width: "45px", height: "45px", animation: "spin 1s linear infinite" }} />
            </div>
          )}

          {!loading && !draft && (
            <div className="glass-panel" style={{ padding: "40px", textAlign: "center", color: "#94a3b8" }}>
              👈 왼쪽 영역에 충전소 고장 증상을 입력하고 초안 생성 버튼을 클릭하면 견적이 생성됩니다.
            </div>
          )}

          {!loading && draft && (
            <div style={{ display: "flex", flexDirection: "column", gap: "24px" }}>
              
              {/* AI Diagnosis details */}
              <section className="glass-panel" style={{ padding: "24px" }}>
                <h3 style={{ fontSize: "16px", fontWeight: "bold", marginBottom: "12px", color: "#06b6d4" }}>🔍 AI 고장 진단 요약</h3>
                <div style={{ fontSize: "14px", lineHeight: "1.6", color: "#cbd5e1" }}>
                  <div style={{ marginBottom: "8px" }}><strong style={{ color: "#f8fafc" }}>증상 요약:</strong> {draft.symptom_summary}</div>
                  <div><strong style={{ color: "#f8fafc" }}>예상 원인:</strong> {draft.likely_cause}</div>
                </div>
              </section>

              {/* Editable Parts Table */}
              <section className="glass-panel" style={{ padding: "24px" }}>
                <h3 style={{ fontSize: "16px", fontWeight: "bold", marginBottom: "16px", color: "#f8fafc" }}>🛠️ 소요 부품 세부 내역</h3>
                {draft.parts.length === 0 ? (
                  <div style={{ padding: "16px", color: "#f59e0b", fontSize: "14px", background: "rgba(245,158,11,0.05)", borderRadius: "6px", border: "1px dashed rgba(245,158,11,0.2)" }}>
                    ⚠️ 예상되는 부품 교체 내역이 없습니다. 단순 현장 점검만 이루어질 경우 공임료만 청구됩니다.
                  </div>
                ) : (
                  <div style={{ display: "flex", flexDirection: "column", gap: "12px" }}>
                    {draft.parts.map((p, idx) => (
                      <div key={idx} style={{ display: "grid", gridTemplateColumns: "3fr 1.5fr 1fr 0.5fr", gap: "16px", alignItems: "center", padding: "12px 16px", background: "rgba(255,255,255,0.02)", borderRadius: "6px", border: "1px solid rgba(255,255,255,0.04)" }}>
                        <div>
                          <div style={{ fontWeight: "bold", color: "#f8fafc", fontSize: "14px" }}>{p.part_name}</div>
                          <div style={{ fontSize: "11px", color: "#64748b", marginTop: "2px" }}>규격: {p.spec} | {p.category}</div>
                        </div>
                        <div style={{ fontSize: "14px", color: "#cbd5e1", textAlign: "right" }}>
                          {(p.unit_price * p.qty).toLocaleString()} 원
                          <span style={{ fontSize: "11px", color: "#64748b", display: "block", marginTop: "2px" }}>(단가: {p.unit_price.toLocaleString()})</span>
                        </div>
                        <div>
                          <input
                            type="number"
                            min="1"
                            value={p.qty}
                            onChange={(e) => handleUpdateQty(idx, Number(e.target.value))}
                            style={{
                              width: "100%",
                              padding: "6px",
                              background: "#1e293b",
                              border: "1px solid rgba(255,255,255,0.08)",
                              borderRadius: "4px",
                              color: "#f8fafc",
                              fontSize: "13px",
                              textAlign: "center"
                            }}
                          />
                        </div>
                        <button
                          onClick={() => handleDeletePart(idx)}
                          style={{
                            background: "transparent",
                            border: "none",
                            color: "#ef4444",
                            cursor: "pointer",
                            fontSize: "14px"
                          }}
                          title="삭제"
                        >
                          🗑️
                        </button>
                      </div>
                    ))}
                  </div>
                )}
              </section>

              {/* Service Fees */}
              <section className="glass-panel" style={{ padding: "24px" }}>
                <h3 style={{ fontSize: "16px", fontWeight: "bold", marginBottom: "16px", color: "#f8fafc" }}>⚡ 기술 서비스료 설정 (출장비 및 공임비)</h3>
                <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "20px" }}>
                  <div>
                    <label style={{ fontSize: "12px", color: "#94a3b8", display: "block", marginBottom: "8px" }}>
                      출장 교통비 (원, 부가세 별도)
                    </label>
                    <input
                      type="number"
                      min="0"
                      step="10000"
                      value={dispatchFee}
                      onChange={(e) => handleUpdateFee("dispatch", Number(e.target.value))}
                      style={{
                        width: "100%",
                        padding: "10px",
                        background: "#1e293b",
                        border: "1px solid rgba(255,255,255,0.08)",
                        borderRadius: "6px",
                        color: "#f8fafc",
                        fontSize: "14px",
                        outline: "none"
                      }}
                    />
                  </div>
                  <div>
                    <label style={{ fontSize: "12px", color: "#94a3b8", display: "block", marginBottom: "8px" }}>
                      작업 공임비 (원, 부가세 별도)
                    </label>
                    <input
                      type="number"
                      min="0"
                      step="10000"
                      value={laborFee}
                      onChange={(e) => handleUpdateFee("labor", Number(e.target.value))}
                      style={{
                        width: "100%",
                        padding: "10px",
                        background: "#1e293b",
                        border: "1px solid rgba(255,255,255,0.08)",
                        borderRadius: "6px",
                        color: "#f8fafc",
                        fontSize: "14px",
                        outline: "none"
                      }}
                    />
                  </div>
                </div>
              </section>

              {/* Summary calculations */}
              <section
                style={{
                  background: "linear-gradient(135deg, rgba(30, 41, 59, 0.7) 0%, rgba(15, 23, 42, 0.9) 100%)",
                  border: "1px solid rgba(255, 255, 255, 0.08)",
                  borderRadius: "12px",
                  padding: "24px",
                  boxShadow: "0 20px 25px -5px rgba(0,0,0,0.3)"
                }}
              >
                <div style={{ display: "flex", justifyContent: "space-between", marginBottom: "12px", fontSize: "14px" }}>
                  <span style={{ color: "#94a3b8" }}>부품비 합계</span>
                  <span style={{ color: "#f8fafc", fontWeight: 600 }}>{partsTotal.toLocaleString()} 원</span>
                </div>
                <div style={{ display: "flex", justifyContent: "space-between", marginBottom: "12px", fontSize: "14px" }}>
                  <span style={{ color: "#94a3b8" }}>기술 서비스료 (출장 + 공임)</span>
                  <span style={{ color: "#f8fafc", fontWeight: 600 }}>{(dispatchFee + laborFee).toLocaleString()} 원</span>
                </div>
                <div
                  style={{
                    height: "1px",
                    background: "rgba(255, 255, 255, 0.08)",
                    margin: "16px 0"
                  }}
                />
                
                <div style={{ display: "flex", justifyContent: "space-between", marginBottom: "10px", fontSize: "15px" }}>
                  <strong style={{ color: "#94a3b8" }}>공급가액 총액</strong>
                  <strong style={{ color: "#38bdf8", fontSize: "18px" }}>{supplyValue.toLocaleString()} 원</strong>
                </div>
                <div style={{ display: "flex", justifyContent: "space-between", marginBottom: "16px", paddingBottom: "12px", borderBottom: "1px dashed rgba(255,255,255,0.08)", fontSize: "15px" }}>
                  <strong style={{ color: "#94a3b8" }}>부가세 (VAT 10%)</strong>
                  <strong style={{ color: "#f97316", fontSize: "18px" }}>{vat.toLocaleString()} 원</strong>
                </div>

                <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginTop: "16px" }}>
                  <span style={{ color: "#f8fafc", fontSize: "18px", fontWeight: "bold" }}>💰 최종 견적 금액 (합계)</span>
                  <span style={{ color: "#4ade80", fontSize: "28px", fontWeight: "900", textShadow: "0 0 16px rgba(74, 222, 128, 0.3)" }}>
                    {grandTotal.toLocaleString()} 원
                  </span>
                </div>
                <div style={{ textAlign: "right", color: "#64748b", fontSize: "11px", marginTop: "8px" }}>
                  * 공급가액 {supplyValue.toLocaleString()}원 + 부가세 {vat.toLocaleString()}원이 가산된 최종 금액입니다.
                </div>
              </section>

              {/* Download Excel button */}
              <button
                onClick={handleDownloadExcel}
                style={{
                  width: "100%",
                  padding: "16px",
                  background: "#10b981",
                  color: "#ffffff",
                  border: "none",
                  borderRadius: "8px",
                  fontWeight: "bold",
                  cursor: "pointer",
                  fontSize: "15px",
                  boxShadow: "0 10px 15px -3px rgba(16,185,129,0.3)",
                  transition: "all 0.2s"
                }}
                onMouseEnter={(e) => { e.currentTarget.style.boxShadow = "0 12px 20px -3px rgba(16,185,129,0.4)"; }}
                onMouseLeave={(e) => { e.currentTarget.style.boxShadow = "0 10px 15px -3px rgba(16,185,129,0.3)"; }}
              >
                📥 견적서 다운로드 (엑셀 템플릿 적용)
              </button>

            </div>
          )}
        </div>
      </div>
    </div>
  );
}
