"use client";

import React, { useEffect, useState } from "react";
import { getApiUrl } from "../utils";

export default function DataManagementPage() {
  const [indexDir, setIndexDir] = useState("csautobot/chroma_db");
  const [activeChroma, setActiveChroma] = useState("");

  useEffect(() => {
    // Attempt to read some info if needed, or show standard information
    setActiveChroma("C:\\deploy\\csautobot\\csautobot\\chroma_db");
  }, []);

  return (
    <div style={{ animation: "fadeIn 0.5s ease-out" }}>
      <header style={{ marginBottom: "36px" }}>
        <h2 style={{ fontSize: "28px", fontWeight: "bold", margin: "0 0 8px 0" }}>📂 학습 데이터 관리</h2>
        <p style={{ color: "#94a3b8", margin: 0, fontSize: "14px" }}>
          AS 원천 데이터 분석 현황과 하이브리드 RAG용 임베딩 인덱스 구성 정보입니다.
        </p>
      </header>

      <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "24px", marginBottom: "24px" }}>
        
        {/* Index Status Card */}
        <section className="glass-panel" style={{ padding: "32px" }}>
          <h3 style={{ fontSize: "18px", fontWeight: "bold", margin: "0 0 20px 0", color: "#f8fafc" }}>⚙️ RAG 인덱스 상태</h3>
          
          <div style={{ display: "flex", flexDirection: "column", gap: "16px", fontSize: "14px" }}>
            <div>
              <span style={{ color: "#94a3b8", display: "block", marginBottom: "4px" }}>활성 인덱스 경로 (ChromaDB)</span>
              <code style={{ background: "#1e293b", padding: "6px 10px", borderRadius: "6px", color: "#06b6d4", wordBreak: "break-all", display: "block" }}>
                {activeChroma}
              </code>
            </div>

            <div>
              <span style={{ color: "#94a3b8", display: "block", marginBottom: "4px" }}>Sparse 인덱스 파일 (BM25)</span>
              <code style={{ background: "#1e293b", padding: "6px 10px", borderRadius: "6px", color: "#cbd5e1", display: "block" }}>
                sparse_index.pkl
              </code>
            </div>

            <div style={{ borderTop: "1px solid rgba(255,255,255,0.06)", paddingTop: "16px" }}>
              <span style={{ color: "#94a3b8", display: "block", marginBottom: "8px" }}>수동 인덱스 업데이트 명령어</span>
              <pre style={{ margin: 0, background: "#0f172a", padding: "12px", borderRadius: "8px", color: "#f8fafc", fontSize: "12px", overflowX: "auto", fontFamily: "monospace" }}>
                # 1. 엑셀 원천 데이터 파싱 및 DB 적재<br />
                python csautobot/ingest.py<br /><br />
                # 2. RAG 임베딩 및 인덱스 재생성<br />
                python csautobot/build_index.py
              </pre>
            </div>
          </div>
        </section>

        {/* Data Architecture Card */}
        <section className="glass-panel" style={{ padding: "32px" }}>
          <h3 style={{ fontSize: "18px", fontWeight: "bold", margin: "0 0 20px 0", color: "#f8fafc" }}>🏛️ 데이터 파이프라인 개요</h3>
          <p style={{ fontSize: "14px", color: "#cbd5e1", lineHeight: "1.7", margin: "0 0 16px 0" }}>
            본 시스템은 현장의 수리 및 정비 엑셀 대장들(`csData/*.xlsx`)로부터 지식을 가공하여 RAG 인프라를 유지합니다:
          </p>
          <ul style={{ fontSize: "14px", color: "#94a3b8", paddingLeft: "20px", display: "flex", flexDirection: "column", gap: "10px", margin: 0 }}>
            <li>
              <strong style={{ color: "#f8fafc" }}>데이터 추출 및 적재</strong>: 엑셀 파일 내의 민원 내용, 상세 조치, 교체 부품 텍스트를 구조화하여 MariaDB / SQLite의 <code>site</code>, <code>charger</code>, <code>incident</code>, <code>action</code> 테이블로 적재합니다.
            </li>
            <li>
              <strong style={{ color: "#f8fafc" }}>하이브리드 임베딩 빌드</strong>: 적재된 데이터를 활용하여 OpenAI Embeddings 모델로 Dense 벡터를 생성해 ChromaDB에 보관하고, 형태소 토큰 단위를 구성하여 BM25 Sparse 모델 피클을 생성합니다.
            </li>
          </ul>
        </section>
      </div>
    </div>
  );
}
