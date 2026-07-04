"use client";

import React, { useState, useEffect } from "react";
import Link from "next/link";
import ContactForm from "./components/ContactForm";

// ─── Sticky Navigation ────────────────────────────────────────────────────────
function StickyNav() {
  const [scrolled, setScrolled] = useState(false);

  useEffect(() => {
    const onScroll = () => setScrolled(window.scrollY > 40);
    window.addEventListener("scroll", onScroll);
    return () => window.removeEventListener("scroll", onScroll);
  }, []);

  const scrollTo = (id: string) =>
    document.getElementById(id)?.scrollIntoView({ behavior: "smooth" });

  return (
    <nav
      style={{
        position: "fixed",
        top: 0,
        left: 0,
        right: 0,
        zIndex: 1000,
        padding: "0 2rem",
        height: "64px",
        display: "flex",
        alignItems: "center",
        justifyContent: "space-between",
        transition: "background 0.3s, box-shadow 0.3s",
        background: scrolled ? "rgba(11,14,20,0.92)" : "transparent",
        backdropFilter: scrolled ? "blur(16px)" : "none",
        boxShadow: scrolled ? "0 1px 0 rgba(255,255,255,0.06)" : "none",
      }}
    >
      <div
        style={{
          fontFamily: "'Outfit', sans-serif",
          fontWeight: 700,
          fontSize: "1.1rem",
        }}
      >
        <span style={{ color: "#06b6d4" }}>CS</span>
        <span style={{ color: "#f8fafc" }}>Autobot</span>
      </div>

      <div style={{ display: "flex", gap: "2rem", alignItems: "center" }}>
        {[
          { label: "제품", id: "services" },
          { label: "가격", id: "pricing" },
          { label: "데모", id: "demo" },
          { label: "도입 상담", id: "contact" },
        ].map((item) => (
          <span
            key={item.id}
            onClick={() => scrollTo(item.id)}
            style={{
              color: "#94a3b8",
              fontSize: "0.9rem",
              fontWeight: 500,
              cursor: "pointer",
              transition: "color 0.2s",
            }}
            onMouseEnter={(e) => (e.currentTarget.style.color = "#f8fafc")}
            onMouseLeave={(e) => (e.currentTarget.style.color = "#94a3b8")}
          >
            {item.label}
          </span>
        ))}
        <Link
          href="/login"
          style={{
            padding: "0.4rem 1.2rem",
            borderRadius: "8px",
            border: "1px solid rgba(255,255,255,0.12)",
            color: "#f8fafc",
            textDecoration: "none",
            fontSize: "0.85rem",
            fontWeight: 600,
          }}
        >
          로그인
        </Link>
      </div>
    </nav>
  );
}

// ─── Main Page ────────────────────────────────────────────────────────────────
interface ChatMessage {
  sender: string;
  text: string;
  data: Record<string, any> | null;
}

const DEMO_STEPS = [
  { sender: "user", text: "RFID 인식 안됨", data: null, delay: 1500 },
  {
    sender: "ai",
    text: "유사 사례를 발견했습니다. 분석 결과는 다음과 같습니다:",
    data: {
      symptom: "회원 카드 및 신용카드 RFID 태그 시 반응 없음",
      causes: [
        "RFID 리더기 보드 통신 케이블 탈거",
        "전면 패널 글라스 오염/스크래치",
        "리더기 펌웨어 멈춤",
      ],
      steps: [
        "내부 CAN/RS232 통신 케이블 접속 상태 확인",
        "리더기 보드 리셋 및 펌웨어 재설치",
        "전면 터치 패널 교체",
      ],
      parts: "RFID Multi-Reader Board (V3.1)",
      evidence: "CS-Case-2023-1102 | 부산 서면 센터",
      confidence: "Mid",
    },
    delay: 3000,
  },
  { sender: "user", text: "에러코드 23", data: null, delay: 6500 },
  {
    sender: "ai",
    text: "유사 사례를 발견했습니다. 분석 결과는 다음과 같습니다:",
    data: {
      symptom: "충전 중 에러코드 23 발생 (전류 과부하 감지)",
      causes: [
        "충전 케이블 내부 단락",
        "차량 OBC(On Board Charger) 통신 오류",
        "충전기 내부 파워모듈 과부하",
      ],
      steps: [
        "충전기 전원 차단 후 케이블 외관 점검",
        "다른 차량에서 동일 에러 발생 여부 확인",
        "파워모듈 출력 전압 테스트 및 캘리브레이션",
      ],
      parts: "충전 케이블 7핀 커넥터 어셈블리",
      evidence: "CS-Case-2024-0512 | 화성 동탄점",
      confidence: "High",
    },
    delay: 8000,
  },
];

const INITIAL_CHAT: ChatMessage[] = [
  {
    sender: "ai",
    text: "안녕하세요! 전기차 충전기 장애 증상이나 에러코드를 입력해 주세요. 유사 사례를 분석하여 조치 방법을 안내해 드립니다.",
    data: null,
  },
];

export default function LandingNewPage() {
  const [isPlaying, setIsPlaying] = useState(false);
  const [chatHistory, setChatHistory] = useState<ChatMessage[]>(INITIAL_CHAT);
  const timeoutIdsRef = React.useRef<NodeJS.Timeout[]>([]);

  const scrollTo = (id: string) =>
    document.getElementById(id)?.scrollIntoView({ behavior: "smooth" });

  const startDemo = () => {
    timeoutIdsRef.current.forEach(clearTimeout);
    timeoutIdsRef.current = [];
    setChatHistory(INITIAL_CHAT);
    setIsPlaying(true);
    DEMO_STEPS.forEach((step) => {
      const id = setTimeout(() => {
        setChatHistory((prev) => [
          ...prev,
          { sender: step.sender, text: step.text, data: step.data },
        ]);
        if (step.delay === 8000) setIsPlaying(false);
      }, step.delay);
      timeoutIdsRef.current.push(id);
    });
  };

  const stopDemo = () => {
    timeoutIdsRef.current.forEach(clearTimeout);
    timeoutIdsRef.current = [];
    setIsPlaying(false);
    setChatHistory(INITIAL_CHAT);
  };

  useEffect(
    () => () => { timeoutIdsRef.current.forEach(clearTimeout); },
    []
  );

  // ── shared styles ──
  const badge = (color: string, bg: string) => ({
    display: "inline-block" as const,
    padding: "0.35rem 1rem",
    background: bg,
    border: `1px solid ${color}60`,
    color,
    borderRadius: "50px",
    fontSize: "0.78rem",
    fontWeight: 700,
    letterSpacing: "1px",
    textTransform: "uppercase" as const,
    marginBottom: "1rem",
  });

  const sectionTitle = {
    fontSize: "clamp(1.8rem, 3vw, 2.8rem)",
    fontWeight: 800,
    color: "#f8fafc",
    fontFamily: "'Outfit', sans-serif",
    marginBottom: "1rem",
  };

  return (
    <div
      style={{
        background: "#0b0e14",
        color: "#e0e0e0",
        fontFamily: "'Inter', sans-serif",
        minHeight: "100vh",
      }}
    >
      <StickyNav />

      {/* ══ ① HERO ══════════════════════════════════════════════════════════ */}
      <section
        style={{
          minHeight: "100vh",
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          position: "relative",
          background:
            "radial-gradient(ellipse at 70% 20%, rgba(6,182,212,0.18) 0%, transparent 55%), radial-gradient(ellipse at 20% 80%, rgba(59,130,246,0.14) 0%, transparent 50%)",
          padding: "80px 2rem 0",
          textAlign: "center",
        }}
      >
        <div
          style={{
            position: "absolute",
            top: "12%",
            right: "8%",
            width: "220px",
            height: "220px",
            background: "#06b6d4",
            filter: "blur(100px)",
            opacity: 0.12,
            borderRadius: "50%",
            pointerEvents: "none",
          }}
        />
        <div
          style={{
            position: "absolute",
            bottom: "15%",
            left: "8%",
            width: "180px",
            height: "180px",
            background: "#3b82f6",
            filter: "blur(90px)",
            opacity: 0.1,
            borderRadius: "50%",
            pointerEvents: "none",
          }}
        />

        <div style={{ zIndex: 1, maxWidth: "860px" }}>
          <span
            style={{
              display: "inline-block",
              padding: "0.45rem 1.4rem",
              background: "rgba(6,182,212,0.08)",
              border: "1px solid rgba(6,182,212,0.4)",
              color: "#06b6d4",
              borderRadius: "50px",
              fontSize: "0.8rem",
              fontWeight: 700,
              marginBottom: "1.8rem",
              letterSpacing: "1.5px",
              textTransform: "uppercase",
            }}
          >
            EV Infrastructure · B2B AI SaaS
          </span>

          <h1
            style={{
              fontSize: "clamp(2.4rem, 5vw, 4.2rem)",
              fontWeight: 800,
              lineHeight: 1.1,
              marginBottom: "1.6rem",
              fontFamily: "'Outfit', sans-serif",
              background:
                "linear-gradient(120deg, #ffffff 30%, #60a5fa, #06b6d4)",
              WebkitBackgroundClip: "text",
              WebkitTextFillColor: "transparent",
            }}
          >
            EV 충전 인프라
            <br />
            AS·점검·견적을 AI로
          </h1>

          <p
            style={{
              fontSize: "1.2rem",
              color: "#94a3b8",
              maxWidth: "640px",
              margin: "0 auto 1rem",
              lineHeight: 1.7,
            }}
          >
            4년치 CS 이력 기반 하이브리드 RAG — 장애 해석부터 점검일지·견적서
            작성까지
            <br />
            한 워크플로로 완결하는{" "}
            <strong style={{ color: "#f8fafc" }}>
              전기차 충전 특화 AI 플랫폼
            </strong>
          </p>

          <p style={{ fontSize: "0.85rem", color: "#475569", marginBottom: "2.8rem" }}>
            충전 인프라 운영사 · AS 협력사 · 콜센터 대상
          </p>

          <div
            style={{
              display: "flex",
              gap: "1rem",
              justifyContent: "center",
              flexWrap: "wrap",
            }}
          >
            <button
              onClick={() => scrollTo("contact")}
              style={{
                padding: "0.9rem 2.4rem",
                borderRadius: "10px",
                fontWeight: 700,
                fontSize: "1rem",
                background: "linear-gradient(135deg, #3b82f6, #06b6d4)",
                color: "#000",
                border: "none",
                cursor: "pointer",
                boxShadow: "0 8px 24px rgba(6,182,212,0.25)",
                transition: "transform 0.2s",
              }}
              onMouseEnter={(e) =>
                (e.currentTarget.style.transform = "translateY(-3px)")
              }
              onMouseLeave={(e) =>
                (e.currentTarget.style.transform = "translateY(0)")
              }
            >
              도입 상담 · 파일럿 문의 →
            </button>
            <button
              onClick={() => scrollTo("demo")}
              style={{
                padding: "0.9rem 2.4rem",
                borderRadius: "10px",
                fontWeight: 600,
                fontSize: "1rem",
                background: "transparent",
                border: "1px solid rgba(255,255,255,0.15)",
                color: "#f8fafc",
                cursor: "pointer",
                transition: "background 0.2s",
              }}
              onMouseEnter={(e) =>
                (e.currentTarget.style.background = "rgba(255,255,255,0.06)")
              }
              onMouseLeave={(e) =>
                (e.currentTarget.style.background = "transparent")
              }
            >
              ▶ 데모 보기
            </button>
            <button
              onClick={() => scrollTo("pricing")}
              style={{
                padding: "0.9rem 2rem",
                borderRadius: "10px",
                fontWeight: 600,
                fontSize: "0.95rem",
                background: "transparent",
                border: "1px solid rgba(255,255,255,0.08)",
                color: "#64748b",
                cursor: "pointer",
                transition: "color 0.2s",
              }}
              onMouseEnter={(e) =>
                (e.currentTarget.style.color = "#94a3b8")
              }
              onMouseLeave={(e) =>
                (e.currentTarget.style.color = "#64748b")
              }
            >
              가격 보기
            </button>
          </div>

          {/* Social proof bar */}
          <div
            style={{
              marginTop: "3.5rem",
              display: "flex",
              gap: "2.5rem",
              justifyContent: "center",
              flexWrap: "wrap",
            }}
          >
            {[
              { val: "4년치", label: "CS 이력 데이터" },
              { val: "5개", label: "AI 업무 모듈" },
              { val: "7.8×", label: "ROI 목표 (가설)" },
            ].map((item) => (
              <div key={item.label} style={{ textAlign: "center" }}>
                <div
                  style={{
                    fontSize: "1.8rem",
                    fontWeight: 800,
                    color: "#06b6d4",
                    fontFamily: "'Outfit', sans-serif",
                  }}
                >
                  {item.val}
                </div>
                <div
                  style={{ fontSize: "0.78rem", color: "#64748b", marginTop: "2px" }}
                >
                  {item.label}
                </div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ══ ② PROBLEM ════════════════════════════════════════════════════════ */}
      <section
        id="problem"
        style={{ padding: "120px 2rem", background: "rgba(15,23,42,0.6)" }}
      >
        <div style={{ maxWidth: "1100px", margin: "0 auto" }}>
          <div style={{ textAlign: "center", marginBottom: "4rem" }}>
            <span style={badge("#ec4899", "rgba(236,72,153,0.08)")}>
              Why Now
            </span>
            <h2 style={sectionTitle}>현장에서 반복되는 5가지 문제</h2>
            <p style={{ color: "#64748b" }}>
              EV 충전 인프라가 늘어날수록, 운영·AS 현장의 비효율도 함께
              커지고 있습니다.
            </p>
          </div>

          <div
            style={{
              display: "grid",
              gridTemplateColumns: "repeat(auto-fit, minmax(280px, 1fr))",
              gap: "1.5rem",
              marginBottom: "4rem",
            }}
          >
            {[
              {
                icon: "⏱️",
                title: "장애 해석 지연",
                desc: "에러코드·증상별 조치법을 찾는 데 시간이 낭비되고, MTTR이 늘어납니다.",
                tag: "MTTR 증가 · SLA 위반",
              },
              {
                icon: "📝",
                title: "점검일지 수기 작성",
                desc: "체크리스트 작성·서명·보고까지 반복되는 수작업이 현장 생산성을 저하시킵니다.",
                tag: "생산성 저하 · 표준화 부재",
              },
              {
                icon: "💸",
                title: "견적·단가 매핑 오류",
                desc: "계약단가표와 엑셀을 수동 대조하다 발생하는 오류가 수익 누수와 고객 분쟁으로 이어집니다.",
                tag: "수익 누수 · 고객 분쟁",
              },
              {
                icon: "🔄",
                title: "재발 장애 파악 어려움",
                desc: "설비별 이력이 흩어져 있어 반복 출동이 발생하고 부품 재고가 비효율적으로 관리됩니다.",
                tag: "반복 출동 · 재고 비효율",
              },
              {
                icon: "📞",
                title: "콜센터 지식 편차",
                desc: "1차 응대 담당자마다 대응 품질이 달라 불필요한 에스컬레이션이 증가합니다.",
                tag: "에스컬레이션 증가",
              },
            ].map((pain) => (
              <div
                key={pain.title}
                style={{
                  padding: "1.8rem",
                  borderRadius: "16px",
                  background: "rgba(255,255,255,0.02)",
                  border: "1px solid rgba(255,255,255,0.06)",
                  transition: "border-color 0.25s, transform 0.25s",
                  cursor: "default",
                }}
                onMouseEnter={(e) => {
                  e.currentTarget.style.borderColor =
                    "rgba(236,72,153,0.3)";
                  e.currentTarget.style.transform = "translateY(-4px)";
                }}
                onMouseLeave={(e) => {
                  e.currentTarget.style.borderColor =
                    "rgba(255,255,255,0.06)";
                  e.currentTarget.style.transform = "translateY(0)";
                }}
              >
                <div style={{ fontSize: "2rem", marginBottom: "0.8rem" }}>
                  {pain.icon}
                </div>
                <h3
                  style={{
                    fontWeight: 700,
                    color: "#f8fafc",
                    fontSize: "1.05rem",
                    marginBottom: "0.6rem",
                  }}
                >
                  {pain.title}
                </h3>
                <p
                  style={{
                    color: "#64748b",
                    fontSize: "0.9rem",
                    lineHeight: 1.6,
                    marginBottom: "1rem",
                  }}
                >
                  {pain.desc}
                </p>
                <span
                  style={{
                    fontSize: "0.75rem",
                    color: "#ec4899",
                    background: "rgba(236,72,153,0.08)",
                    padding: "0.2rem 0.7rem",
                    borderRadius: "50px",
                  }}
                >
                  {pain.tag}
                </span>
              </div>
            ))}
          </div>

          {/* Target personas */}
          <div
            style={{
              borderTop: "1px solid rgba(255,255,255,0.06)",
              paddingTop: "3rem",
              textAlign: "center",
            }}
          >
            <p
              style={{
                color: "#64748b",
                fontSize: "0.85rem",
                marginBottom: "2rem",
                textTransform: "uppercase",
                letterSpacing: "1px",
              }}
            >
              CSAutobot 도입 대상
            </p>
            <div
              style={{
                display: "flex",
                gap: "1rem",
                justifyContent: "center",
                flexWrap: "wrap",
              }}
            >
              {[
                {
                  icon: "🏢",
                  label: "충전 인프라 운영사",
                  sub: "SLA·대시보드·재발 장애",
                },
                {
                  icon: "🔧",
                  label: "AS · 정비 협력사",
                  sub: "유사 사례·견적·일지 표준화",
                },
                {
                  icon: "🎧",
                  label: "콜센터 · 1차 응대",
                  sub: "빠른 진단·에스컬레이션 기준",
                },
              ].map((p) => (
                <div
                  key={p.label}
                  style={{
                    padding: "1rem 1.8rem",
                    borderRadius: "12px",
                    background: "rgba(255,255,255,0.02)",
                    border: "1px solid rgba(255,255,255,0.07)",
                    textAlign: "center",
                    minWidth: "200px",
                  }}
                >
                  <div style={{ fontSize: "1.6rem", marginBottom: "0.5rem" }}>
                    {p.icon}
                  </div>
                  <div
                    style={{
                      fontWeight: 700,
                      color: "#f8fafc",
                      fontSize: "0.95rem",
                    }}
                  >
                    {p.label}
                  </div>
                  <div
                    style={{ fontSize: "0.78rem", color: "#64748b", marginTop: "4px" }}
                  >
                    {p.sub}
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      </section>

      {/* ══ ③ SERVICES ══════════════════════════════════════════════════════ */}
      <section
        id="services"
        style={{ padding: "120px 2rem", background: "#0b0e14" }}
      >
        <div style={{ maxWidth: "1100px", margin: "0 auto" }}>
          <div style={{ textAlign: "center", marginBottom: "4rem" }}>
            <span style={badge("#06b6d4", "rgba(6,182,212,0.08)")}>
              5대 AI 모듈
            </span>
            <h2 style={sectionTitle}>
              장애 → AI 제안 → 확정 → 저장
              <br />
              한 워크플로로 완결
            </h2>
            <p style={{ color: "#64748b" }}>
              AI는 권고하고, 최종 판단·책임은 현장 엔지니어가 합니다.
            </p>
          </div>

          <div
            style={{
              display: "grid",
              gridTemplateColumns: "repeat(auto-fit, minmax(300px, 1fr))",
              gap: "1.5rem",
            }}
          >
            {[
              {
                num: "01",
                icon: "🔍",
                title: "AS 유사 사례 검색",
                desc: "증상·에러코드 입력 → 하이브리드 RAG(Dense+BM25)로 유사 사례 즉시 검색. 근거 사례·신뢰도 함께 제공.",
                tag: "핵심 차별화",
                accent: "#06b6d4",
              },
              {
                num: "02",
                icon: "📋",
                title: "점검일지 AI 어시스턴트",
                desc: "체크리스트·메모·사진 입력 → AI가 이상징후·권장 조치·후속 점검 초안 자동 생성. 엔지니어가 수정·확정.",
                tag: "현장 생산성",
                accent: "#3b82f6",
              },
              {
                num: "03",
                icon: "💰",
                title: "AI 견적서 생성기",
                desc: "증상 → 부품 추론 → 계약단가표 자동 매핑. 출장비·공임비·VAT까지 포함한 견적서 초안을 즉시 생성.",
                tag: "수익 직결",
                accent: "#10b981",
              },
              {
                num: "04",
                icon: "📊",
                title: "운영 대시보드",
                desc: "점검·장애·피드백 데이터 시각화. MTTR·FTFR·재발 장애·위험도를 한눈에 파악해 의사결정 속도를 높입니다.",
                tag: "운영 인사이트",
                accent: "#f59e0b",
              },
              {
                num: "05",
                icon: "🗄️",
                title: "학습 데이터 관리",
                desc: "원천 데이터·RAG 인덱스 관리. CS 이력이 쌓일수록 검색 품질이 향상되는 데이터 자산 축적 구조.",
                tag: "데이터 자산",
                accent: "#ec4899",
              },
            ].map((mod) => (
              <div
                key={mod.num}
                style={{
                  padding: "2rem",
                  borderRadius: "18px",
                  background: "rgba(255,255,255,0.02)",
                  border: "1px solid rgba(255,255,255,0.06)",
                  transition: "border-color 0.25s, transform 0.25s",
                  position: "relative",
                  overflow: "hidden",
                  cursor: "default",
                }}
                onMouseEnter={(e) => {
                  e.currentTarget.style.borderColor = `${mod.accent}55`;
                  e.currentTarget.style.transform = "translateY(-4px)";
                }}
                onMouseLeave={(e) => {
                  e.currentTarget.style.borderColor =
                    "rgba(255,255,255,0.06)";
                  e.currentTarget.style.transform = "translateY(0)";
                }}
              >
                <div
                  style={{
                    position: "absolute",
                    top: "1.2rem",
                    right: "1.5rem",
                    fontSize: "0.7rem",
                    color: "rgba(255,255,255,0.08)",
                    fontWeight: 800,
                    fontFamily: "'Outfit', sans-serif",
                  }}
                >
                  {mod.num}
                </div>
                <div style={{ fontSize: "1.8rem", marginBottom: "0.8rem" }}>
                  {mod.icon}
                </div>
                <h3
                  style={{
                    fontWeight: 700,
                    color: "#f8fafc",
                    fontSize: "1.05rem",
                    marginBottom: "0.6rem",
                  }}
                >
                  {mod.title}
                </h3>
                <p
                  style={{
                    color: "#64748b",
                    fontSize: "0.88rem",
                    lineHeight: 1.65,
                    marginBottom: "1.2rem",
                  }}
                >
                  {mod.desc}
                </p>
                <span
                  style={{
                    fontSize: "0.75rem",
                    color: mod.accent,
                    background: `${mod.accent}18`,
                    padding: "0.2rem 0.7rem",
                    borderRadius: "50px",
                  }}
                >
                  {mod.tag}
                </span>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ══ ③.Ⅴ ENTERPRISE EXTENSION ══════════════════════════════════════════════════════ */}
      <section
        style={{ padding: "40px 2rem 120px", background: "#0b0e14" }}
      >
        <div style={{ maxWidth: "1100px", margin: "0 auto" }}>
          <div style={{ textAlign: "center", marginBottom: "4rem" }}>
            <span style={badge("#a855f7", "rgba(168,85,247,0.08)")}>
              엔터프라이즈 확장
            </span>
            <h2 style={sectionTitle}>
              제조사·운영사·플릿을 위한<br />맞춤형 AI 확장 모듈
            </h2>
            <p style={{ color: "#64748b" }}>
              CSAutobot 엔진을 자사 시스템에 통합하거나 특정 목적의 대시보드로 구성합니다.
            </p>
          </div>

          <div
            style={{
              display: "grid",
              gridTemplateColumns: "repeat(auto-fit, minmax(300px, 1fr))",
              gap: "1.5rem",
            }}
          >
            {[
              {
                target: "대형 CPO",
                icon: "🔌",
                title: "Headless AI API",
                desc: "자사 CSMS에 AI 엔진을 이식하여 전국망 MTTR을 단축하고, 지자체/기관의 위약금(SLA 페널티) 등 치명적인 리스크를 방어합니다.",
                tag: "SLA 위약금 방어",
                accent: "#06b6d4",
              },
              {
                target: "충전기 제조사",
                icon: "🏭",
                title: "결함 분석 (Defect Analytics)",
                desc: "모델별 빈발 장애와 부품 불량률을 추적하여, 무상 보증 기간 내 발생하는 막대한 과잉 수리 비용(Warranty Cost)을 사전에 차단합니다.",
                tag: "보증 비용 절감",
                accent: "#f59e0b",
              },
              {
                target: "플릿 운영사 (버스/택시)",
                icon: "🚍",
                title: "가동률 중심 예지 정비",
                desc: "고장 발생 전 이상 징후를 선제적으로 알람하여, 충전 불가로 인한 차량 배차 차질과 즉각적인 현금 영업 손실을 막아냅니다.",
                tag: "영업 손실 방어",
                accent: "#10b981",
              },
            ].map((mod, idx) => (
              <div
                key={idx}
                style={{
                  padding: "2rem",
                  borderRadius: "18px",
                  background: "linear-gradient(145deg, rgba(255,255,255,0.03) 0%, rgba(255,255,255,0.01) 100%)",
                  border: "1px solid rgba(255,255,255,0.06)",
                  transition: "border-color 0.25s, transform 0.25s",
                  position: "relative",
                }}
                onMouseEnter={(e) => {
                  e.currentTarget.style.borderColor = `${mod.accent}55`;
                  e.currentTarget.style.transform = "translateY(-4px)";
                }}
                onMouseLeave={(e) => {
                  e.currentTarget.style.borderColor = "rgba(255,255,255,0.06)";
                  e.currentTarget.style.transform = "translateY(0)";
                }}
              >
                <div style={{ fontSize: "2rem", marginBottom: "1rem" }}>{mod.icon}</div>
                <div style={{ fontSize: "0.8rem", color: mod.accent, fontWeight: "bold", marginBottom: "0.3rem" }}>{mod.target}</div>
                <h3 style={{ fontSize: "1.1rem", fontWeight: 700, color: "#f8fafc", marginBottom: "0.8rem" }}>{mod.title}</h3>
                <p style={{ color: "#94a3b8", fontSize: "0.88rem", lineHeight: 1.6, marginBottom: "1.2rem" }}>{mod.desc}</p>
                <span style={{ fontSize: "0.75rem", color: "#e2e8f0", background: "rgba(255,255,255,0.05)", padding: "0.3rem 0.8rem", borderRadius: "50px" }}>{mod.tag}</span>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ══ ④ ROI + KPI ══════════════════════════════════════════════════════ */}
      <section
        style={{
          padding: "120px 2rem",
          background:
            "linear-gradient(180deg, rgba(15,23,42,0.7) 0%, #0b0e14 100%)",
        }}
      >
        <div style={{ maxWidth: "1100px", margin: "0 auto" }}>
          <div style={{ textAlign: "center", marginBottom: "4rem" }}>
            <span style={badge("#10b981", "rgba(16,185,129,0.08)")}>
              가치 제안 · ROI
            </span>
            <h2 style={sectionTitle}>Pro 구독 1년, 투자 대비 7.8배 효과</h2>
            <p style={{ color: "#64748b", fontSize: "0.85rem" }}>
              엔지니어 10명 기준 가설 시나리오 — 실제 효과는 환경에 따라
              다릅니다.
            </p>
          </div>

          {/* ROI Box */}
          <div
            style={{
              background:
                "linear-gradient(135deg, rgba(6,182,212,0.06), rgba(59,130,246,0.06))",
              border: "1px solid rgba(6,182,212,0.2)",
              borderRadius: "20px",
              padding: "2.5rem 3rem",
              marginBottom: "3rem",
              display: "grid",
              gridTemplateColumns: "repeat(auto-fit, minmax(160px, 1fr))",
              gap: "2rem",
              textAlign: "center",
            }}
          >
            {[
              { label: "점검일지 절감", val: "1,200시간/년", sub: "≈ 7,200만 원" },
              { label: "1차 응대 단축", val: "500시간/년", sub: "≈ 3,000만 원" },
              { label: "재출동 감소", val: "5% 절감", sub: "≈ 240만 원" },
              { label: "Pro 구독료", val: "연 1,188만 원", sub: "99만/월 × 12" },
              {
                label: "순 ROI (가설)",
                val: "≈ 9,200만 원",
                sub: "약 7.8배",
                highlight: true,
              },
            ].map((r) => (
              <div key={r.label}>
                <div
                  style={{
                    fontSize: "0.72rem",
                    color: "#64748b",
                    textTransform: "uppercase",
                    letterSpacing: "1px",
                    marginBottom: "0.4rem",
                  }}
                >
                  {r.label}
                </div>
                <div
                  style={{
                    fontSize: r.highlight ? "1.5rem" : "1.2rem",
                    fontWeight: 800,
                    color: r.highlight ? "#06b6d4" : "#f8fafc",
                    fontFamily: "'Outfit', sans-serif",
                  }}
                >
                  {r.val}
                </div>
                <div
                  style={{
                    fontSize: "0.75rem",
                    color: r.highlight ? "#10b981" : "#475569",
                    marginTop: "3px",
                  }}
                >
                  {r.sub}
                </div>
              </div>
            ))}
          </div>

          {/* KPI Cards */}
          <div
            style={{
              display: "grid",
              gridTemplateColumns: "repeat(auto-fit, minmax(220px, 1fr))",
              gap: "1.5rem",
              marginBottom: "1rem",
            }}
          >
            {[
              { label: "FTFR (초기 수리 성공률)", val: "84.2%", delta: "▲ 22.5% vs 전분기" },
              { label: "MTTR (평균 수리 시간)", val: "42m", delta: "▼ 15분 단축" },
              { label: "AI 답변 신뢰도", val: "91.7%", delta: "▲ 5.4% vs 전분기" },
              { label: "미해결 티켓 감소", val: "-35%", delta: "지난 3개월간" },
            ].map((kpi) => (
              <div
                key={kpi.label}
                style={{
                  padding: "1.8rem",
                  borderRadius: "16px",
                  background: "rgba(255,255,255,0.02)",
                  border: "1px solid rgba(255,255,255,0.06)",
                  textAlign: "center",
                }}
              >
                <div
                  style={{
                    fontSize: "0.72rem",
                    color: "#64748b",
                    textTransform: "uppercase",
                    letterSpacing: "1px",
                    marginBottom: "0.5rem",
                  }}
                >
                  {kpi.label}
                </div>
                <div
                  style={{
                    fontSize: "2.6rem",
                    fontWeight: 800,
                    color: "#06b6d4",
                    fontFamily: "'Outfit', sans-serif",
                  }}
                >
                  {kpi.val}
                </div>
                <div
                  style={{ fontSize: "0.8rem", color: "#10b981", marginTop: "0.6rem" }}
                >
                  {kpi.delta}
                </div>
              </div>
            ))}
          </div>
          <p style={{ textAlign: "center", fontSize: "0.75rem", color: "#334155" }}>
            * 위 KPI는 파일럿 목표치(가설)이며, 데모 시나리오 기준입니다.
            실운영 환경에 따라 달라질 수 있습니다.
          </p>
        </div>
      </section>

      {/* ══ ⑤ DEMO ══════════════════════════════════════════════════════════ */}
      <section
        id="demo"
        style={{
          padding: "120px 2rem",
          background: "linear-gradient(180deg, #0b0e14, #131722)",
        }}
      >
        <div style={{ maxWidth: "1100px", margin: "0 auto" }}>
          <div style={{ textAlign: "center", marginBottom: "4rem" }}>
            <span style={badge("#60a5fa", "rgba(59,130,246,0.08)")}>
              Interactive Demo
            </span>
            <h2 style={sectionTitle}>AS 검색 AI 직접 체험</h2>
            <p style={{ color: "#64748b" }}>
              전기차 충전기 장애 증상·에러코드를 입력하면 AI가 유사 사례와
              조치 가이드를 제안합니다.
            </p>
          </div>

          <div
            style={{
              maxWidth: "780px",
              margin: "0 auto",
              background: "#151922",
              borderRadius: "24px",
              overflow: "hidden",
              boxShadow: "0 30px 60px rgba(0,0,0,0.5)",
              display: "flex",
              flexDirection: "column",
              height: "580px",
            }}
          >
            {/* Chat Header */}
            <div
              style={{
                padding: "1.2rem 1.8rem",
                background: "rgba(255,255,255,0.02)",
                borderBottom: "1px solid rgba(255,255,255,0.07)",
                display: "flex",
                alignItems: "center",
                justifyContent: "space-between",
                flexWrap: "wrap",
                gap: "0.8rem",
              }}
            >
              <div
                style={{ display: "flex", alignItems: "center", gap: "0.8rem" }}
              >
                <div
                  style={{
                    width: "9px",
                    height: "9px",
                    background: isPlaying ? "#3b82f6" : "#10b981",
                    borderRadius: "50%",
                    boxShadow: isPlaying
                      ? "0 0 8px #3b82f6"
                      : "0 0 8px #10b981",
                  }}
                />
                <div>
                  <div
                    style={{
                      fontWeight: 700,
                      color: "#f8fafc",
                      fontSize: "0.95rem",
                    }}
                  >
                    AS 지원 에이전트 v2.0
                  </div>
                  <div style={{ fontSize: "0.75rem", color: "#64748b" }}>
                    하이브리드 RAG (4년 CS 이력 기반) · 시뮬레이션 모드
                  </div>
                </div>
              </div>
              <div>
                {!isPlaying ? (
                  <button
                    onClick={startDemo}
                    style={{
                      fontSize: "0.8rem",
                      background:
                        "linear-gradient(135deg, #3b82f6, #06b6d4)",
                      border: "none",
                      padding: "0.4rem 1rem",
                      borderRadius: "6px",
                      color: "#000",
                      fontWeight: "bold",
                      cursor: "pointer",
                    }}
                  >
                    ▶ 데모 시작
                  </button>
                ) : (
                  <button
                    onClick={stopDemo}
                    style={{
                      fontSize: "0.8rem",
                      background: "rgba(239,68,68,0.15)",
                      border: "1px solid #ef4444",
                      padding: "0.4rem 1rem",
                      borderRadius: "6px",
                      color: "#ef4444",
                      fontWeight: "bold",
                      cursor: "pointer",
                    }}
                  >
                    ■ 정지 및 리셋
                  </button>
                )}
              </div>
            </div>

            {/* Chat body */}
            <div
              style={{
                flex: 1,
                padding: "1.5rem",
                overflowY: "auto",
                display: "flex",
                flexDirection: "column",
                gap: "1.2rem",
              }}
            >
              {chatHistory.map((msg, idx) => (
                <div
                  key={idx}
                  style={{
                    alignSelf:
                      msg.sender === "user" ? "flex-end" : "flex-start",
                    background:
                      msg.sender === "user"
                        ? "#3b82f6"
                        : "rgba(255,255,255,0.03)",
                    border:
                      msg.sender === "user"
                        ? "none"
                        : "1px solid rgba(255,255,255,0.07)",
                    color: msg.sender === "user" ? "#000" : "#e0e0e0",
                    maxWidth: "82%",
                    padding: "0.9rem 1.3rem",
                    borderRadius: "14px",
                    borderBottomRightRadius:
                      msg.sender === "user" ? "4px" : "14px",
                    borderBottomLeftRadius:
                      msg.sender === "ai" ? "4px" : "14px",
                    fontSize: "0.9rem",
                    lineHeight: 1.5,
                  }}
                >
                  {msg.text}
                  {msg.data && (
                    <div
                      style={{
                        marginTop: "1.2rem",
                        borderTop: "1px solid rgba(255,255,255,0.07)",
                        paddingTop: "1.2rem",
                      }}
                    >
                      {[
                        {
                          label: "🔍 증상 요약",
                          content: (
                            <p style={{ color: "#94a3b8", margin: 0 }}>
                              {msg.data.symptom}
                            </p>
                          ),
                        },
                        {
                          label: "⚠️ 추정 원인",
                          content: (
                            <ul
                              style={{
                                margin: 0,
                                paddingLeft: "1.2rem",
                                color: "#94a3b8",
                              }}
                            >
                              {msg.data.causes.map(
                                (c: string, i: number) => (
                                  <li key={i}>{c}</li>
                                )
                              )}
                            </ul>
                          ),
                        },
                        {
                          label: "🛠️ 점검/조치 순서",
                          content: (
                            <ol
                              style={{
                                margin: 0,
                                paddingLeft: "1.2rem",
                                color: "#94a3b8",
                              }}
                            >
                              {msg.data.steps.map(
                                (s: string, i: number) => (
                                  <li key={i}>{s}</li>
                                )
                              )}
                            </ol>
                          ),
                        },
                        {
                          label: "📦 필요 부품",
                          content: (
                            <p style={{ color: "#94a3b8", margin: 0 }}>
                              {msg.data.parts}
                            </p>
                          ),
                        },
                      ].map((sec) => (
                        <div key={sec.label} style={{ marginBottom: "0.8rem" }}>
                          <span
                            style={{
                              fontWeight: 700,
                              color: "#06b6d4",
                              display: "block",
                              marginBottom: "0.3rem",
                              fontSize: "0.85rem",
                            }}
                          >
                            {sec.label}
                          </span>
                          {sec.content}
                        </div>
                      ))}
                      <div
                        style={{
                          fontSize: "0.72rem",
                          color: "#475569",
                          marginTop: "0.8rem",
                        }}
                      >
                        📚 근거 사례: {msg.data.evidence}
                      </div>
                      <div
                        style={{
                          display: "inline-flex",
                          alignItems: "center",
                          padding: "0.2rem 0.7rem",
                          borderRadius: "50px",
                          fontSize: "0.72rem",
                          fontWeight: 600,
                          marginTop: "0.6rem",
                          background:
                            msg.data.confidence === "High"
                              ? "rgba(16,185,129,0.1)"
                              : "rgba(245,158,11,0.1)",
                          color:
                            msg.data.confidence === "High"
                              ? "#10b981"
                              : "#f59e0b",
                        }}
                      >
                        ● 신뢰도: {msg.data.confidence} · AI 권고 / 최종 판단은 엔지니어가 합니다
                      </div>
                    </div>
                  )}
                </div>
              ))}
            </div>

            {/* Input bar */}
            <div
              style={{
                padding: "1.2rem 1.8rem",
                borderTop: "1px solid rgba(255,255,255,0.07)",
                display: "flex",
                gap: "0.8rem",
              }}
            >
              <input
                type="text"
                disabled
                placeholder={
                  isPlaying
                    ? "데모 시뮬레이션 진행 중..."
                    : "'데모 시작' 버튼을 누르면 시나리오가 재생됩니다."
                }
                style={{
                  flex: 1,
                  background: "rgba(255,255,255,0.02)",
                  border: "1px solid rgba(255,255,255,0.05)",
                  padding: "0.65rem 1.2rem",
                  borderRadius: "10px",
                  color: "#475569",
                  outline: "none",
                  cursor: "not-allowed",
                  fontSize: "0.85rem",
                }}
              />
              <button
                disabled
                style={{
                  background: "rgba(255,255,255,0.02)",
                  color: "#475569",
                  border: "none",
                  padding: "0 1.2rem",
                  borderRadius: "10px",
                  fontWeight: 700,
                  cursor: "not-allowed",
                }}
              >
                전송
              </button>
            </div>
          </div>
        </div>
      </section>

      {/* ══ ⑥ PRICING ════════════════════════════════════════════════════════ */}
      <section
        id="pricing"
        style={{ padding: "120px 2rem", background: "rgba(15,23,42,0.5)" }}
      >
        <div style={{ maxWidth: "1100px", margin: "0 auto" }}>
          <div style={{ textAlign: "center", marginBottom: "4rem" }}>
            <span style={badge("#f59e0b", "rgba(245,158,11,0.08)")}>
              요금제
            </span>
            <h2 style={sectionTitle}>투명한 가격, 유연한 도입</h2>
            <p style={{ color: "#64748b", fontSize: "0.85rem" }}>
              VAT 별도 · 연간 선납 시 10% 할인 · 가격은 파일럿 후 확정될 수
              있습니다 (가설안)
            </p>
          </div>

          <div
            style={{
              display: "grid",
              gridTemplateColumns: "repeat(auto-fit, minmax(280px, 1fr))",
              gap: "1.5rem",
              marginBottom: "4rem",
            }}
          >
            {[
              {
                name: "Free",
                price: "0원",
                period: "무료",
                desc: "PoC 관심사·소규모 협력사",
                accent: "#64748b",
                badge: null,
                annualNote: null,
                features: [
                  "충전기 최대 50기",
                  "사용자 최대 3명",
                  "AS 검색 월 100회",
                  "AI 생성 월 10회",
                  "기본 대시보드 (7일)",
                  "커뮤니티 지원",
                ],
                cta: "무료로 시작",
                highlight: false,
              },
              {
                name: "Pro",
                price: "990,000원",
                period: "/월",
                desc: "실운영 현장·AS 협력사",
                accent: "#06b6d4",
                badge: "추천",
                annualNote: "연납 시 891,000원/월",
                features: [
                  "충전기 최대 500기",
                  "사용자 20명 포함",
                  "+50,000원/인 추가",
                  "AS 검색 월 5,000회",
                  "AI 생성 월 500회",
                  "점검일지 AI · 견적서",
                  "월간 리포트",
                  "이메일·채팅 지원 (영업일)",
                ],
                cta: "파일럿 문의",
                highlight: true,
              },
              {
                name: "Enterprise",
                price: "3,500,000원~",
                period: "/월",
                desc: "대형 운영사·보안 요구 고객",
                accent: "#ec4899",
                badge: null,
                annualNote: null,
                features: [
                  "충전기·사용자 무제한",
                  "AI 생성 무제한",
                  "Pro 전체 포함",
                  "전담 CSM · 4시간 P1 대응",
                  "전용 SLA · RBAC · 감사로그",
                  "API · ERP 연동",
                  "온프렘/VPC 옵션",
                  "연간 계약",
                ],
                cta: "도입 상담 문의",
                highlight: false,
              },
            ].map((plan) => (
              <div
                key={plan.name}
                style={{
                  padding: "2.2rem",
                  borderRadius: "20px",
                  background: plan.highlight
                    ? "linear-gradient(145deg, rgba(6,182,212,0.06), rgba(59,130,246,0.06))"
                    : "rgba(255,255,255,0.02)",
                  border: plan.highlight
                    ? "1px solid rgba(6,182,212,0.35)"
                    : "1px solid rgba(255,255,255,0.07)",
                  position: "relative",
                  display: "flex",
                  flexDirection: "column",
                }}
              >
                {plan.badge && (
                  <div
                    style={{
                      position: "absolute",
                      top: "-12px",
                      left: "50%",
                      transform: "translateX(-50%)",
                      background:
                        "linear-gradient(135deg, #3b82f6, #06b6d4)",
                      color: "#000",
                      padding: "0.25rem 1rem",
                      borderRadius: "50px",
                      fontSize: "0.75rem",
                      fontWeight: 700,
                      whiteSpace: "nowrap",
                    }}
                  >
                    {plan.badge}
                  </div>
                )}
                <div style={{ marginBottom: "1.5rem" }}>
                  <div
                    style={{
                      fontSize: "0.8rem",
                      color: plan.accent,
                      fontWeight: 700,
                      textTransform: "uppercase",
                      letterSpacing: "1px",
                      marginBottom: "0.5rem",
                    }}
                  >
                    {plan.name}
                  </div>
                  <div
                    style={{
                      display: "flex",
                      alignItems: "baseline",
                      gap: "0.3rem",
                    }}
                  >
                    <span
                      style={{
                        fontSize: "1.8rem",
                        fontWeight: 800,
                        color: "#f8fafc",
                        fontFamily: "'Outfit', sans-serif",
                      }}
                    >
                      {plan.price}
                    </span>
                    <span
                      style={{ color: "#64748b", fontSize: "0.85rem" }}
                    >
                      {plan.period}
                    </span>
                  </div>
                  {plan.annualNote && (
                    <div
                      style={{
                        fontSize: "0.78rem",
                        color: "#10b981",
                        marginTop: "4px",
                      }}
                    >
                      {plan.annualNote}
                    </div>
                  )}
                  <div
                    style={{
                      fontSize: "0.82rem",
                      color: "#64748b",
                      marginTop: "0.5rem",
                    }}
                  >
                    {plan.desc}
                  </div>
                </div>
                <ul
                  style={{
                    listStyle: "none",
                    padding: 0,
                    margin: "0 0 2rem",
                    flex: 1,
                  }}
                >
                  {plan.features.map((f) => (
                    <li
                      key={f}
                      style={{
                        display: "flex",
                        gap: "0.6rem",
                        color: "#94a3b8",
                        fontSize: "0.85rem",
                        marginBottom: "0.5rem",
                      }}
                    >
                      <span
                        style={{ color: plan.accent, flexShrink: 0 }}
                      >
                        ✓
                      </span>
                      {f}
                    </li>
                  ))}
                </ul>
                <button
                  onClick={() => scrollTo("contact")}
                  style={{
                    width: "100%",
                    padding: "0.8rem",
                    borderRadius: "10px",
                    fontWeight: 700,
                    fontSize: "0.9rem",
                    cursor: "pointer",
                    border: "none",
                    background: plan.highlight
                      ? "linear-gradient(135deg, #3b82f6, #06b6d4)"
                      : "rgba(255,255,255,0.05)",
                    color: plan.highlight ? "#000" : "#94a3b8",
                    transition: "opacity 0.2s",
                  }}
                  onMouseEnter={(e) =>
                    (e.currentTarget.style.opacity = "0.85")
                  }
                  onMouseLeave={(e) =>
                    (e.currentTarget.style.opacity = "1")
                  }
                >
                  {plan.cta}
                </button>
              </div>
            ))}
          </div>

          {/* Pilot box */}
          <div
            style={{
              borderRadius: "20px",
              background: "rgba(236,72,153,0.04)",
              border: "1px solid rgba(236,72,153,0.15)",
              padding: "2.5rem 3rem",
            }}
          >
            <div
              style={{
                display: "grid",
                gridTemplateColumns: "repeat(auto-fit, minmax(260px, 1fr))",
                gap: "2rem",
                alignItems: "center",
              }}
            >
              <div>
                <div
                  style={{
                    fontSize: "0.75rem",
                    color: "#ec4899",
                    textTransform: "uppercase",
                    letterSpacing: "1px",
                    marginBottom: "0.8rem",
                  }}
                >
                  파일럿 프로그램
                </div>
                <h3
                  style={{
                    fontWeight: 800,
                    color: "#f8fafc",
                    fontSize: "1.4rem",
                    marginBottom: "0.6rem",
                    fontFamily: "'Outfit', sans-serif",
                  }}
                >
                  3개월 파일럿으로 시작하세요
                </h3>
                <p
                  style={{
                    color: "#64748b",
                    fontSize: "0.88rem",
                    lineHeight: 1.6,
                  }}
                >
                  KPI 미달 시 유료 전환 의무 없음. 전환 시 파일럿 비용의{" "}
                  <strong style={{ color: "#f8fafc" }}>
                    50%를 첫 연 구독료에서 차감
                  </strong>
                </p>
              </div>
              <div style={{ display: "flex", gap: "1.2rem", flexWrap: "wrap" }}>
                {[
                  {
                    name: "스탠다드",
                    price: "600만 원",
                    period: "/3개월 (VAT 별도)",
                    items: ["클라우드 배포", "KPI 리포트 1회", "교육 2회"],
                  },
                  {
                    name: "프리미엄",
                    price: "1,200만 원",
                    period: "/3개월 (VAT 별도)",
                    items: [
                      "전용 데이터 적재",
                      "Top-3 적중률 평가",
                      "ROI 리포트",
                    ],
                  },
                ].map((pilot) => (
                  <div
                    key={pilot.name}
                    style={{
                      flex: 1,
                      minWidth: "180px",
                      padding: "1.4rem",
                      borderRadius: "14px",
                      background: "rgba(255,255,255,0.02)",
                      border: "1px solid rgba(255,255,255,0.07)",
                    }}
                  >
                    <div
                      style={{
                        fontSize: "0.75rem",
                        color: "#ec4899",
                        fontWeight: 700,
                        marginBottom: "0.4rem",
                      }}
                    >
                      {pilot.name}
                    </div>
                    <div
                      style={{
                        fontSize: "1.4rem",
                        fontWeight: 800,
                        color: "#f8fafc",
                        fontFamily: "'Outfit', sans-serif",
                      }}
                    >
                      {pilot.price}
                    </div>
                    <div
                      style={{
                        fontSize: "0.72rem",
                        color: "#475569",
                        marginBottom: "0.8rem",
                      }}
                    >
                      {pilot.period}
                    </div>
                    <ul style={{ listStyle: "none", padding: 0, margin: 0 }}>
                      {pilot.items.map((item) => (
                        <li
                          key={item}
                          style={{
                            fontSize: "0.8rem",
                            color: "#64748b",
                            marginBottom: "0.3rem",
                          }}
                        >
                          ✓ {item}
                        </li>
                      ))}
                    </ul>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* ══ ⑦ TRUST ══════════════════════════════════════════════════════════ */}
      <section style={{ padding: "120px 2rem", background: "#0b0e14" }}>
        <div style={{ maxWidth: "1100px", margin: "0 auto" }}>
          <div style={{ textAlign: "center", marginBottom: "4rem" }}>
            <span style={badge("#ec4899", "rgba(236,72,153,0.08)")}>
              Why CSAutobot
            </span>
            <h2 style={sectionTitle}>범용 AI·CMMS와 무엇이 다른가요?</h2>
          </div>

          <div style={{ overflowX: "auto", marginBottom: "6rem" }}>
            <table
              style={{
                width: "100%",
                borderCollapse: "collapse",
                minWidth: "600px",
              }}
            >
              <thead>
                <tr>
                  {[
                    "비교 항목",
                    "범용 LLM (ChatGPT 등)",
                    "일반 CMMS·티켓",
                    "CSAutobot ✓",
                  ].map((h, i) => (
                    <th
                      key={h}
                      style={{
                        padding: "1rem 1.2rem",
                        textAlign: i === 0 ? "left" : "center",
                        fontSize: "0.85rem",
                        fontWeight: 700,
                        color: i === 3 ? "#06b6d4" : "#64748b",
                        borderBottom: "1px solid rgba(255,255,255,0.07)",
                        background:
                          i === 3 ? "rgba(6,182,212,0.04)" : "transparent",
                      }}
                    >
                      {h}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {[
                  ["EV 도메인 지식", "❌ 범용", "△ 매뉴얼", "✅ 4년 CS 이력 RAG"],
                  ["유사 사례 검색", "❌", "△ 텍스트 검색", "✅ 하이브리드 Dense+BM25"],
                  ["점검일지 AI 초안", "△ 프롬프트 의존", "❌", "✅ 워크플로 통합"],
                  ["견적서 자동 생성", "❌", "△ 수동 입력", "✅ 계약단가 자동 매핑"],
                  ["데이터 보안·온프렘", "❌ 외부 API", "△", "✅ 로컬 LLM 전환 경로"],
                  ["신뢰도·근거 표시", "△", "❌", "✅ 사례 출처·신뢰도 등급"],
                ].map((row, ri) => (
                  <tr
                    key={ri}
                    style={{ borderBottom: "1px solid rgba(255,255,255,0.04)" }}
                  >
                    {row.map((cell, ci) => (
                      <td
                        key={ci}
                        style={{
                          padding: "0.9rem 1.2rem",
                          fontSize: "0.88rem",
                          textAlign: ci === 0 ? "left" : "center",
                          color:
                            ci === 0
                              ? "#94a3b8"
                              : ci === 3
                              ? "#10b981"
                              : "#475569",
                          background:
                            ci === 3
                              ? "rgba(6,182,212,0.03)"
                              : "transparent",
                          fontWeight: ci === 3 ? 600 : 400,
                        }}
                      >
                        {cell}
                      </td>
                    ))}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          {/* Architecture */}
          <div
            style={{
              display: "grid",
              gridTemplateColumns: "repeat(auto-fit, minmax(300px, 1fr))",
              gap: "3rem",
              alignItems: "center",
            }}
          >
            <div>
              <span style={badge("#ec4899", "rgba(236,72,153,0.08)")}>
                System Architecture
              </span>
              <h3
                style={{
                  fontSize: "1.8rem",
                  fontWeight: 800,
                  color: "#f8fafc",
                  marginBottom: "1rem",
                  fontFamily: "'Outfit', sans-serif",
                }}
              >
                Secure RAG Pipeline
              </h3>
              <p
                style={{
                  color: "#94a3b8",
                  lineHeight: 1.7,
                  marginBottom: "2rem",
                  fontSize: "0.9rem",
                }}
              >
                민감한 AS 데이터를 외부 유출 없이 처리하기 위해 로컬 LLM
                전환 경로를 확보했습니다. 하이브리드 검색과 재순위화 엔진으로
                답변 정확도를 극대화합니다.
              </p>
              <div style={{ display: "flex", flexWrap: "wrap", gap: "0.6rem" }}>
                {[
                  "LangChain",
                  "Qwen 2.5 (14B)",
                  "Ollama",
                  "Chroma DB",
                  "FastAPI",
                  "Next.js",
                  "BM25 Hybrid",
                ].map((tag) => (
                  <span
                    key={tag}
                    style={{
                      padding: "0.35rem 0.9rem",
                      background: "rgba(255,255,255,0.04)",
                      border: "1px solid rgba(255,255,255,0.08)",
                      borderRadius: "8px",
                      fontSize: "0.8rem",
                      color: "#94a3b8",
                    }}
                  >
                    {tag}
                  </span>
                ))}
              </div>
            </div>

            <div
              style={{
                padding: "2.5rem",
                borderRadius: "20px",
                background: "rgba(255,255,255,0.01)",
                border: "1px solid rgba(255,255,255,0.06)",
              }}
            >
              {[
                { num: "1", title: "Hybrid Retrieval", desc: "Dense(벡터) + Sparse(BM25) 동시 검색" },
                { num: "2", title: "Embedding Rerank", desc: "코사인 유사도 정밀 재순위화" },
                { num: "3", title: "Confidence Scoring", desc: "검색 분포 기반 신뢰도 등급 산출" },
                { num: "4", title: "Structured Generation", desc: "LLM 통한 정형화 점검 가이드 생성" },
              ].map((step) => (
                <div
                  key={step.num}
                  style={{
                    display: "flex",
                    gap: "1.2rem",
                    marginBottom: "1.6rem",
                  }}
                >
                  <div
                    style={{
                      width: "36px",
                      height: "36px",
                      background: "rgba(6,182,212,0.08)",
                      border: "1px solid #06b6d4",
                      borderRadius: "50%",
                      display: "flex",
                      alignItems: "center",
                      justifyContent: "center",
                      color: "#06b6d4",
                      fontWeight: "bold",
                      fontSize: "0.85rem",
                      flexShrink: 0,
                    }}
                  >
                    {step.num}
                  </div>
                  <div>
                    <div
                      style={{
                        fontWeight: 700,
                        color: "#f8fafc",
                        fontSize: "0.95rem",
                      }}
                    >
                      {step.title}
                    </div>
                    <div
                      style={{
                        fontSize: "0.82rem",
                        color: "#64748b",
                        marginTop: "3px",
                      }}
                    >
                      {step.desc}
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      </section>

      {/* ══ ⑧ CONTACT ════════════════════════════════════════════════════════ */}
      <section
        id="contact"
        style={{
          padding: "120px 2rem 80px",
          background:
            "linear-gradient(180deg, rgba(15,23,42,0.7), #0b0e14)",
        }}
      >
        <div style={{ maxWidth: "760px", margin: "0 auto" }}>
          <div style={{ textAlign: "center", marginBottom: "4rem" }}>
            <span style={badge("#06b6d4", "rgba(6,182,212,0.08)")}>
              도입 상담
            </span>
            <h2 style={sectionTitle}>파일럿으로 먼저 검증하세요</h2>
            <p style={{ color: "#64748b" }}>
              KPI 미달 시 유료 전환 의무 없습니다. 먼저 결과로 확인하세요.
            </p>
          </div>

          <ContactForm />
        </div>
      </section>

      {/* ── Footer ──────────────────────────────────────────────────────────── */}
      <footer
        style={{
          padding: "3rem 2rem",
          borderTop: "1px solid rgba(255,255,255,0.06)",
          background: "#0b0e14",
        }}
      >
        <div
          style={{
            maxWidth: "1100px",
            margin: "0 auto",
            display: "flex",
            justifyContent: "space-between",
            alignItems: "center",
            flexWrap: "wrap",
            gap: "1.5rem",
          }}
        >
          <div>
            <div
              style={{
                fontFamily: "'Outfit', sans-serif",
                fontWeight: 700,
                fontSize: "1.1rem",
                marginBottom: "0.4rem",
              }}
            >
              <span style={{ color: "#06b6d4" }}>CS</span>
              <span style={{ color: "#f8fafc" }}>Autobot</span>
            </div>
            <p style={{ fontSize: "0.78rem", color: "#334155", margin: 0 }}>
              EV 충전 인프라 특화 AI 운영 플랫폼 · B2B SaaS
            </p>
          </div>

          <div style={{ display: "flex", gap: "2rem", flexWrap: "wrap" }}>
            {[
              { label: "제품 소개", id: "services" },
              { label: "가격", id: "pricing" },
              { label: "데모", id: "demo" },
              { label: "도입 상담", id: "contact" },
            ].map((item) => (
              <span
                key={item.id}
                onClick={() => scrollTo(item.id)}
                style={{ fontSize: "0.82rem", color: "#475569", cursor: "pointer" }}
                onMouseEnter={(e) => (e.currentTarget.style.color = "#94a3b8")}
                onMouseLeave={(e) => (e.currentTarget.style.color = "#475569")}
              >
                {item.label}
              </span>
            ))}
            <Link
              href="/login"
              style={{
                fontSize: "0.82rem",
                color: "#475569",
                textDecoration: "none",
              }}
            >
              로그인
            </Link>
          </div>

          <div style={{ textAlign: "right" }}>
            <p style={{ fontSize: "0.78rem", color: "#334155", margin: 0 }}>
              © 2026 CSAutobot. All rights reserved.
            </p>
            <p
              style={{ fontSize: "0.72rem", color: "#1e293b", margin: "4px 0 0" }}
            >
              가격·KPI는 파일럿 가설치이며 VAT 별도입니다.
            </p>
          </div>
        </div>
      </footer>
    </div>
  );
}
