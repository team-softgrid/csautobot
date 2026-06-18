"use client";

import React from "react";
import Link from "next/link";

export default function AdminHomePage() {
  const cards = [
    {
      title: "📊 운영 대시보드",
      description: "전체 점검 현황과 필터링 지표, Altair 기반 차트 및 피드백 현황을 시각화합니다.",
      path: "/dashboard",
      color: "#06b6d4",
    },
    {
      title: "📝 점검일지 AI 어시스턴트",
      description: "설비 체크리스트와 사진을 첨부하면 위험도를 자동 분석하고 요약 초안을 작성합니다.",
      path: "/inspection",
      color: "#3b82f6",
    },
    {
      title: "🔎 AS 유사 사례 검색",
      description: "장애 상황을 자유롭게 입력하면 과거 정비기록(RAG)과 실시간 웹 지식을 결합해 조치 방안을 제시합니다.",
      path: "/search",
      color: "#ec4899",
    },
    {
      title: "📂 학습 데이터 관리",
      description: "원천 AS 데이터 및 RAG 임베딩 인덱스 구성 상태를 점검하고 관리합니다.",
      path: "/data-management",
      color: "#10b981",
    },
  ];

  return (
    <div style={{ animation: "fadeIn 0.5s ease-out" }}>
      {/* Hero Header */}
      <header style={{ marginBottom: "48px" }}>
        <h2 style={{ fontSize: "36px", fontWeight: "bold", margin: "0 0 12px 0", color: "#f8fafc" }}>
          Next Generation EV Ops AI
        </h2>
        <p style={{ fontSize: "16px", color: "#94a3b8", margin: 0, lineHeight: "1.6", maxWidth: "800px" }}>
          전기차 충전소 정기점검 · 고장 AS · 민원 대응을 하나의 유기적인 워크플로우로 연결합니다.
          현장 체크리스트와 현장 사진을 기반으로 위험도 판정 및 AI 정비 가이드를 제시하고,
          과거 정비 이력은 하이브리드 RAG 검색으로 즉시 참조 가능합니다.
        </p>
      </header>

      {/* Navigation Grid */}
      <section style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(280px, 1fr))", gap: "24px", marginBottom: "48px" }}>
        {cards.map((card, i) => (
          <Link href={card.path} key={i} style={{ textDecoration: "none" }}>
            <div
              className="glass-panel"
              style={{
                padding: "32px",
                height: "100%",
                display: "flex",
                flexDirection: "column",
                cursor: "pointer",
              }}
            >
              <h3
                style={{
                  fontSize: "20px",
                  fontWeight: "bold",
                  color: card.color,
                  margin: "0 0 12px 0",
                }}
              >
                {card.title}
              </h3>
              <p
                style={{
                  fontSize: "14px",
                  color: "#94a3b8",
                  margin: 0,
                  lineHeight: "1.6",
                  flex: 1,
                }}
              >
                {card.description}
              </p>
              <div
                style={{
                  marginTop: "24px",
                  fontSize: "13px",
                  fontWeight: "bold",
                  color: card.color,
                  display: "flex",
                  alignItems: "center",
                  gap: "4px",
                }}
              >
                바로가기 →
              </div>
            </div>
          </Link>
        ))}
      </section>

      {/* Info Panel */}
      <section
        className="glass-panel"
        style={{
          padding: "32px",
          borderLeft: "4px solid #06b6d4",
        }}
      >
        <h4 style={{ fontSize: "18px", fontWeight: "bold", margin: "0 0 12px 0", color: "#f8fafc" }}>
          ⚡ 아키텍처 공지
        </h4>
        <p style={{ fontSize: "14px", color: "#94a3b8", margin: 0, lineHeight: "1.7" }}>
          본 프론트엔드는 Streamlit 기반 PoC 아키텍처를 엔터프라이즈 상용 스택인 **Next.js 14 App Router + FastAPI** 구조로 완전 전환하여 제작되었습니다.
          기존의 로컬 데이터베이스 쿼리 방식 대신 비동기 REST API 클라이언트 통신을 적용하여 성능과 보안 및 동시 처리량이 대폭 극대화되었습니다.
        </p>
      </section>
    </div>
  );
}
