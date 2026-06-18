"use client";

import React, { useState } from "react";
import Link from "next/link";

export default function LandingPage() {
  interface ChatMessage {
    sender: string;
    text: string;
    data: any;
  }

  const [chatInput, setChatInput] = useState("");
  const [chatHistory, setChatHistory] = useState<ChatMessage[]>([
    {
      sender: "ai",
      text: "안녕하세요! 전기차 충전기 장애 증상이나 에러코드를 입력해 주세요. 유사 사례를 분석하여 조치 방법을 안내해 드립니다.",
      data: null,
    },
  ]);

  const mockScenarios: Record<string, any> = {
    "에러코드 23": {
      symptom: "충전 중 에러코드 23 발생 (전류 과부하 감지)",
      causes: ["충전 케이블 내부 단락", "차량 OBC(On Board Charger) 통신 오류", "충전기 내부 파워모듈 과부하"],
      steps: ["충전기 전원 차단 후 케이블 외관 점검", "다른 차량에서 동일 에러 발생 여부 확인", "파워모듈 출력 전압 테스트 및 캘리브레이션"],
      parts: "충전 케이블 7핀 커넥터 어셈블리",
      evidence: "CS-Case-2024-0512 | 화성 동탄점",
      confidence: "High",
    },
    "RFID 인식 안됨": {
      symptom: "회원 카드 및 신용카드 RFID 태그 시 반응 없음",
      causes: ["RFID 리더기 보드 통신 케이블 탈거", "전면 패널 글라스 오염/스크래치", "리더기 펌웨어 멈춤"],
      steps: ["내부 CAN/RS232 통신 케이블 접속 상태 확인", "리더기 보드 리셋 및 펌웨어 재설치", "전면 터치 패널 교체"],
      parts: "RFID Multi-Reader Board (V3.1)",
      evidence: "CS-Case-2023-1102 | 부산 서면 센터",
      confidence: "Mid",
    },
    "부팅 안됨": {
      symptom: "전원 투입 후 메인 화면 및 LED 인디케이터 점등 안됨",
      causes: ["SMPS(Switching Mode Power Supply) 출력 불량", "메인보드 입력 단자 휴즈 단선", "AC 입력 전원 결상"],
      steps: ["분전함 차단기 확인 및 입력 전압 측정", "SMPS DC 12V/24V 출력 전압 체크", "메인보드 휴즈 상태 점검 및 교체"],
      parts: "Industrial SMPS 24V 150W",
      evidence: "CS-Case-2024-0215 | 서울 강남 주차장",
      confidence: "High",
    },
  };

  const handleSend = () => {
    const text = chatInput.trim();
    if (!text) return;

    // User message
    const updatedHistory = [...chatHistory, { sender: "user", text, data: null }];
    setChatHistory(updatedHistory);
    setChatInput("");

    // Simulate AI response
    setTimeout(() => {
      const matchedKey = Object.keys(mockScenarios).find((key) => text.includes(key));
      if (matchedKey) {
        setChatHistory((prev) => [
          ...prev,
          {
            sender: "ai",
            text: "유사 사례를 발견했습니다. 분석 결과는 다음과 같습니다:",
            data: mockScenarios[matchedKey],
          },
        ]);
      } else {
        setChatHistory((prev) => [
          ...prev,
          {
            sender: "ai",
            text: "죄송합니다. 입력하신 증상에 대한 직접적인 유사 사례를 찾지 못했습니다. 보다 상세한 증상이나 다른 키워드로 입력해 주시겠습니까? (예: 에러코드 23, RFID 인식 안됨, 부팅 안됨)",
            data: null,
          },
        ]);
      }
    }, 800);
  };

  return (
    <div style={{ background: "#0b0e14", color: "#e0e0e0", fontFamily: "'Inter', sans-serif", minHeight: "100vh" }}>
      
      {/* Hero Section */}
      <section style={{
        height: "100vh",
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        position: "relative",
        background: "radial-gradient(circle at top right, rgba(6, 182, 212, 0.15), transparent), radial-gradient(circle at bottom left, rgba(236, 72, 153, 0.1), transparent)",
        padding: "0 2rem",
        textAlign: "center"
      }}>
        <div style={{
          position: "absolute",
          top: "10%",
          right: "10%",
          width: "150px",
          height: "150px",
          background: "#06b6d4",
          filter: "blur(80px)",
          opacity: 0.15,
          borderRadius: "50%"
        }}></div>
        <div style={{
          position: "absolute",
          bottom: "10%",
          left: "10%",
          width: "150px",
          height: "150px",
          background: "#ec4899",
          filter: "blur(80px)",
          opacity: 0.1,
          borderRadius: "50%"
        }}></div>

        <div style={{ zIndex: 1, maxWidth: "800px" }}>
          <span style={{
            display: "inline-block",
            padding: "0.5rem 1.5rem",
            background: "rgba(6, 182, 212, 0.1)",
            border: "1px solid #06b6d4",
            color: "#06b6d4",
            borderRadius: "50px",
            fontSize: "0.9rem",
            fontWeight: 600,
            marginBottom: "1.5rem",
            textTransform: "uppercase",
            letterSpacing: "1px"
          }}>
            Next Generation AI Support
          </span>
          <h1 style={{
            fontSize: "4rem",
            fontWeight: "bold",
            lineHeight: "1.1",
            marginBottom: "1.5rem",
            background: "linear-gradient(to right, #fff, #3b82f6, #06b6d4)",
            WebkitBackgroundClip: "text",
            WebkitTextFillColor: "transparent",
            fontFamily: "'Outfit', sans-serif"
          }}>
            EV Infrastructure<br />Technical Copilot
          </h1>
          <p style={{
            fontSize: "1.25rem",
            color: "#94a3b8",
            maxWidth: "700px",
            margin: "0 auto 3rem",
            lineHeight: "1.6"
          }}>
            전기차 충전 인프라 장애 해결의 새로운 패러다임.<br />
            국내 최대 AS 데이터베이스와 로컬 LLM이 결합된 맞춤형 기술 지원 솔루션.
          </p>
          <div style={{ display: "flex", gap: "1.5rem", justifyContent: "center", flexWrap: "wrap" }}>
            <Link href="/admin" style={{
              padding: "1rem 2.5rem",
              borderRadius: "8px",
              fontWeight: 700,
              textDecoration: "none",
              background: "linear-gradient(135deg, #3b82f6, #06b6d4)",
              color: "#000000",
              boxShadow: "0 10px 20px rgba(6, 182, 212, 0.2)",
              transition: "transform 0.2s",
            }}
            onMouseEnter={(e) => e.currentTarget.style.transform = "translateY(-3px)"}
            onMouseLeave={(e) => e.currentTarget.style.transform = "translateY(0)"}
            >
              관리자 대시보드 바로가기 →
            </Link>
            <a href="#demo" style={{
              padding: "1rem 2.5rem",
              borderRadius: "8px",
              fontWeight: 700,
              textDecoration: "none",
              background: "transparent",
              border: "1px solid rgba(255, 255, 255, 0.1)",
              color: "#ffffff",
              transition: "background 0.2s"
            }}
            onMouseEnter={(e) => e.currentTarget.style.background = "rgba(255,255,255,0.05)"}
            onMouseLeave={(e) => e.currentTarget.style.background = "transparent"}
            >
              실시간 데모 확인
            </a>
          </div>
        </div>
      </section>

      {/* KPI Stats Section */}
      <section style={{ padding: "100px 2rem", background: "rgba(15, 23, 42, 0.5)" }}>
        <div style={{ maxWidth: "1200px", margin: "0 auto" }}>
          <div style={{ textAlign: "center", marginBottom: "4rem" }}>
            <h2 style={{ fontSize: "2.5rem", fontWeight: "bold", marginBottom: "1rem", color: "#f8fafc", fontFamily: "'Outfit', sans-serif" }}>
              Real-time Intelligence
            </h2>
            <p style={{ color: "#94a3b8" }}>AI 도입 후 개선된 유지보수 효율 지표</p>
          </div>

          <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(240px, 1fr))", gap: "2rem" }}>
            <div className="glass-panel" style={{ padding: "2rem", borderRadius: "20px", background: "rgba(255,255,255,0.02)" }}>
              <div style={{ color: "#94a3b8", fontSize: "0.85rem", textTransform: "uppercase", letterSpacing: "1px", marginBottom: "0.5rem" }}>
                FTFR (초기 수리 성공률)
              </div>
              <div style={{ fontSize: "3rem", fontWeight: "bold", color: "#06b6d4", fontFamily: "'Outfit', sans-serif" }}>
                84.2%
              </div>
              <div style={{ color: "#10b981", fontSize: "0.85rem", marginTop: "1rem" }}>
                ▲ 22.5% vs 전분기
              </div>
            </div>

            <div className="glass-panel" style={{ padding: "2rem", borderRadius: "20px", background: "rgba(255,255,255,0.02)" }}>
              <div style={{ color: "#94a3b8", fontSize: "0.85rem", textTransform: "uppercase", letterSpacing: "1px", marginBottom: "0.5rem" }}>
                MTTR (평균 수리 시간)
              </div>
              <div style={{ fontSize: "3rem", fontWeight: "bold", color: "#06b6d4", fontFamily: "'Outfit', sans-serif" }}>
                42m
              </div>
              <div style={{ color: "#10b981", fontSize: "0.85rem", marginTop: "1rem" }}>
                ▼ 15m vs 전분기
              </div>
            </div>

            <div className="glass-panel" style={{ padding: "2rem", borderRadius: "20px", background: "rgba(255,255,255,0.02)" }}>
              <div style={{ color: "#94a3b8", fontSize: "0.85rem", textTransform: "uppercase", letterSpacing: "1px", marginBottom: "0.5rem" }}>
                AI 답변 신뢰도
              </div>
              <div style={{ fontSize: "3rem", fontWeight: "bold", color: "#06b6d4", fontFamily: "'Outfit', sans-serif" }}>
                91.7%
              </div>
              <div style={{ color: "#10b981", fontSize: "0.85rem", marginTop: "1rem" }}>
                ▲ 5.4% vs 전분기
              </div>
            </div>

            <div className="glass-panel" style={{ padding: "2rem", borderRadius: "20px", background: "rgba(255,255,255,0.02)" }}>
              <div style={{ color: "#94a3b8", fontSize: "0.85rem", textTransform: "uppercase", letterSpacing: "1px", marginBottom: "0.5rem" }}>
                미해결 티켓 감소
              </div>
              <div style={{ fontSize: "3rem", fontWeight: "bold", color: "#06b6d4", fontFamily: "'Outfit', sans-serif" }}>
                -35%
              </div>
              <div style={{ color: "#10b981", fontSize: "0.85rem", marginTop: "1rem" }}>
                지난 3개월간
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Interactive Demo Section */}
      <section id="demo" style={{ padding: "100px 2rem", background: "linear-gradient(180deg, #0b0e14, #131722)" }}>
        <div style={{ maxWidth: "1200px", margin: "0 auto" }}>
          <div style={{ textAlign: "center", marginBottom: "4rem" }}>
            <h2 style={{ fontSize: "2.5rem", fontWeight: "bold", marginBottom: "1rem", color: "#f8fafc", fontFamily: "'Outfit', sans-serif" }}>
              Interactive Demo
            </h2>
            <p style={{ color: "#94a3b8" }}>기존 csData AS Bot 로직이 적용된 기술 지원 에이전트 모크 데모</p>
          </div>

          <div className="glass-panel" style={{
            maxWidth: "800px",
            margin: "0 auto",
            background: "#151922",
            borderRadius: "24px",
            overflow: "hidden",
            boxShadow: "0 30px 60px rgba(0, 0, 0, 0.4)",
            display: "flex",
            flexDirection: "column",
            height: "600px"
          }}>
            {/* Chat Header */}
            <div style={{
              padding: "1.5rem 2rem",
              background: "rgba(255, 255, 255, 0.02)",
              borderBottom: "1px solid rgba(255, 255, 255, 0.08)",
              display: "flex",
              alignItems: "center",
              justifyContent: "space-between"
            }}>
              <div style={{ display: "flex", alignItems: "center", gap: "1rem" }}>
                <div style={{
                  width: "10px",
                  height: "10px",
                  background: "#10b981",
                  borderRadius: "50%",
                  boxShadow: "0 0 10px #10b981"
                }}></div>
                <div>
                  <div style={{ fontWeight: 700, color: "#f8fafc" }}>AS 지원 에이전트 v2.0</div>
                  <div style={{ fontSize: "0.8rem", color: "#94a3b8" }}>Local LLM (Qwen 2.5) + RAG Enabled</div>
                </div>
              </div>
              <div style={{ fontSize: "0.8rem", background: "rgba(255,255,255,0.05)", padding: "0.3rem 0.8rem", borderRadius: "4px", color: "#94a3b8" }}>
                Enterprise Secure
              </div>
            </div>

            {/* Chat History */}
            <div style={{
              flex: 1,
              padding: "2rem",
              overflowY: "auto",
              display: "flex",
              flexDirection: "column",
              gap: "1.5rem"
            }}>
              {chatHistory.map((msg, idx) => (
                <div
                  key={idx}
                  style={{
                    alignSelf: msg.sender === "user" ? "flex-end" : "flex-start",
                    background: msg.sender === "user" ? "#3b82f6" : "rgba(255, 255, 255, 0.03)",
                    border: msg.sender === "user" ? "none" : "1px solid rgba(255,255,255,0.08)",
                    color: msg.sender === "user" ? "#000" : "#e0e0e0",
                    maxWidth: "80%",
                    padding: "1rem 1.5rem",
                    borderRadius: "16px",
                    borderBottomRightRadius: msg.sender === "user" ? "4px" : "16px",
                    borderBottomLeftRadius: msg.sender === "ai" ? "4px" : "16px",
                    fontSize: "0.95rem",
                    lineHeight: "1.5"
                  }}
                >
                  {msg.text}

                  {msg.data && (
                    <div style={{
                      marginTop: "1.5rem",
                      borderTop: "1px solid rgba(255, 255, 255, 0.08)",
                      paddingTop: "1.5rem"
                    }}>
                      <span style={{ fontWeight: 700, color: "#06b6d4", marginBottom: "0.5rem", display: "block" }}>
                        🔍 증상 요약
                      </span>
                      <p style={{ marginBottom: "1rem", color: "#94a3b8" }}>{msg.data.symptom}</p>

                      <span style={{ fontWeight: 700, color: "#06b6d4", marginBottom: "0.5rem", display: "block" }}>
                        ⚠️ 추정 원인
                      </span>
                      <ul style={{ marginBottom: "1rem", paddingLeft: "1.2rem", color: "#94a3b8" }}>
                        {msg.data.causes.map((c: string, cIdx: number) => <li key={cIdx}>{c}</li>)}
                      </ul>

                      <span style={{ fontWeight: 700, color: "#06b6d4", marginBottom: "0.5rem", display: "block" }}>
                        🛠️ 점검/조치 순서
                      </span>
                      <ol style={{ marginBottom: "1rem", paddingLeft: "1.2rem", color: "#94a3b8" }}>
                        {msg.data.steps.map((s: string, sIdx: number) => <li key={sIdx}>{s}</li>)}
                      </ol>

                      <span style={{ fontWeight: 700, color: "#06b6d4", marginBottom: "0.5rem", display: "block" }}>
                        📦 필요 부품
                      </span>
                      <p style={{ marginBottom: "1rem", color: "#94a3b8" }}>{msg.data.parts}</p>

                      <div style={{ fontSize: "0.8rem", color: "#64748b", marginTop: "1rem" }}>
                        📚 근거 사례: {msg.data.evidence}
                      </div>

                      <div style={{
                        display: "inline-flex",
                        alignItems: "center",
                        padding: "0.25rem 0.75rem",
                        borderRadius: "50px",
                        fontSize: "0.8rem",
                        fontWeight: 600,
                        marginTop: "1rem",
                        background: msg.data.confidence === "High" ? "rgba(16, 185, 129, 0.1)" : "rgba(245, 158, 11, 0.1)",
                        color: msg.data.confidence === "High" ? "#10b981" : "#f59e0b"
                      }}>
                        ● 신뢰도: {msg.data.confidence}
                      </div>
                    </div>
                  )}
                </div>
              ))}
            </div>

            {/* Chat Input */}
            <div style={{
              padding: "1.5rem 2rem",
              background: "rgba(255, 255, 255, 0.02)",
              borderTop: "1px solid rgba(255, 255, 255, 0.08)",
              display: "flex",
              gap: "1rem"
            }}>
              <input
                type="text"
                value={chatInput}
                onChange={(e) => setChatInput(e.target.value)}
                onKeyPress={(e) => e.key === "Enter" && handleSend()}
                placeholder="증상 또는 에러코드를 입력하세요 (예: 에러코드 23, RFID 인식 안됨, 부팅 안됨)"
                style={{
                  flex: 1,
                  background: "rgba(255, 255, 255, 0.05)",
                  border: "1px solid rgba(255, 255, 255, 0.08)",
                  padding: "0.75rem 1.5rem",
                  borderRadius: "12px",
                  color: "#fff",
                  outline: "none",
                  transition: "border-color 0.3s"
                }}
                onFocus={(e) => e.currentTarget.style.borderColor = "#06b6d4"}
                onBlur={(e) => e.currentTarget.style.borderColor = "rgba(255, 255, 255, 0.08)"}
              />
              <button
                onClick={handleSend}
                style={{
                  background: "#06b6d4",
                  color: "#000",
                  border: "none",
                  padding: "0 1.5rem",
                  borderRadius: "12px",
                  fontWeight: 700,
                  cursor: "pointer"
                }}
              >
                전송
              </button>
            </div>
          </div>
        </div>
      </section>

      {/* System Architecture Section */}
      <section style={{ padding: "100px 2rem", background: "#0b0e14" }}>
        <div style={{ maxWidth: "1200px", margin: "0 auto" }}>
          <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(300px, 1fr))", gap: "3rem", alignItems: "center" }}>
            <div>
              <div style={{
                display: "inline-block",
                padding: "0.5rem 1.5rem",
                background: "rgba(240, 147, 251, 0.1)",
                border: "1px solid #ec4899",
                color: "#ec4899",
                borderRadius: "50px",
                fontSize: "0.9rem",
                fontWeight: 600,
                marginBottom: "1.5rem",
                textTransform: "uppercase",
                letterSpacing: "1px"
              }}>
                System Architecture
              </div>
              <h2 style={{ fontSize: "2.5rem", fontWeight: "bold", marginBottom: "1.5rem", color: "#f8fafc", fontFamily: "'Outfit', sans-serif" }}>
                Secure RAG Pipeline
              </h2>
              <p style={{ color: "#94a3b8", marginBottom: "2rem", lineHeight: "1.7" }}>
                민감한 AS 데이터를 외부 유출 없이 처리하기 위해 로컬 LLM 환경을 최우선으로 설계했습니다.
                하이브리드 검색과 재순위화 엔진을 통해 답변의 정확도를 극대화합니다.
              </p>
              <div style={{ display: "flex", flexWrap: "wrap", gap: "0.75rem" }}>
                <span style={{ padding: "0.4rem 1rem", background: "rgba(255, 255, 255, 0.05)", border: "1px solid #ec4899", borderRadius: "8px", fontSize: "0.85rem", color: "#ec4899" }}>LangChain</span>
                <span style={{ padding: "0.4rem 1rem", background: "rgba(255, 255, 255, 0.05)", border: "1px solid rgba(255,255,255,0.08)", borderRadius: "8px", fontSize: "0.85rem", color: "#94a3b8" }}>Qwen 2.5 (14B)</span>
                <span style={{ padding: "0.4rem 1rem", background: "rgba(255, 255, 255, 0.05)", border: "1px solid rgba(255,255,255,0.08)", borderRadius: "8px", fontSize: "0.85rem", color: "#94a3b8" }}>Ollama</span>
                <span style={{ padding: "0.4rem 1rem", background: "rgba(255, 255, 255, 0.05)", border: "1px solid rgba(255,255,255,0.08)", borderRadius: "8px", fontSize: "0.85rem", color: "#94a3b8" }}>Chroma DB</span>
                <span style={{ padding: "0.4rem 1rem", background: "rgba(255, 255, 255, 0.05)", border: "1px solid rgba(255,255,255,0.08)", borderRadius: "8px", fontSize: "0.85rem", color: "#94a3b8" }}>FastAPI</span>
                <span style={{ padding: "0.4rem 1rem", background: "rgba(255, 255, 255, 0.05)", border: "1px solid rgba(255,255,255,0.08)", borderRadius: "8px", fontSize: "0.85rem", color: "#94a3b8" }}>Next.js</span>
              </div>
            </div>

            <div className="glass-panel" style={{ padding: "3rem", borderRadius: "24px", background: "rgba(255,255,255,0.01)" }}>
              <div style={{ display: "flex", gap: "1.5rem", marginBottom: "2rem" }}>
                <div style={{ width: "40px", height: "40px", background: "rgba(255,255,255,0.02)", border: "1px solid #06b6d4", borderRadius: "50%", display: "flex", alignItems: "center", justifyContent: "center", color: "#06b6d4", fontWeight: "bold" }}>1</div>
                <div>
                  <div style={{ fontWeight: 700, color: "#f8fafc" }}>Hybrid Retrieval</div>
                  <div style={{ fontSize: "0.85rem", color: "#94a3b8", marginTop: "4px" }}>Dense(벡터) + Sparse(BM25) 동시 검색</div>
                </div>
              </div>

              <div style={{ display: "flex", gap: "1.5rem", marginBottom: "2rem" }}>
                <div style={{ width: "40px", height: "40px", background: "rgba(255,255,255,0.02)", border: "1px solid #06b6d4", borderRadius: "50%", display: "flex", alignItems: "center", justifyContent: "center", color: "#06b6d4", fontWeight: "bold" }}>2</div>
                <div>
                  <div style={{ fontWeight: 700, color: "#f8fafc" }}>Embedding Rerank</div>
                  <div style={{ fontSize: "0.85rem", color: "#94a3b8", marginTop: "4px" }}>상위 후보군에 대한 코사인 유사도 정밀 재순위화</div>
                </div>
              </div>

              <div style={{ display: "flex", gap: "1.5rem", marginBottom: "2rem" }}>
                <div style={{ width: "40px", height: "40px", background: "rgba(255,255,255,0.02)", border: "1px solid #06b6d4", borderRadius: "50%", display: "flex", alignItems: "center", justifyContent: "center", color: "#06b6d4", fontWeight: "bold" }}>3</div>
                <div>
                  <div style={{ fontWeight: 700, color: "#f8fafc" }}>Confidence Scoring</div>
                  <div style={{ fontSize: "0.85rem", color: "#94a3b8", marginTop: "4px" }}>검색 분포 기반 답변 신뢰도 등급 산출</div>
                </div>
              </div>

              <div style={{ display: "flex", gap: "1.5rem" }}>
                <div style={{ width: "40px", height: "40px", background: "rgba(255,255,255,0.02)", border: "1px solid #06b6d4", borderRadius: "50%", display: "flex", alignItems: "center", justifyContent: "center", color: "#06b6d4", fontWeight: "bold" }}>4</div>
                <div>
                  <div style={{ fontWeight: 700, color: "#f8fafc" }}>Structured Generation</div>
                  <div style={{ fontSize: "0.85rem", color: "#94a3b8", marginTop: "4px" }}>Local LLM을 통한 정형화된 점검 가이드 생성</div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer style={{ padding: "4rem 0", textAlign: "center", borderTop: "1px solid rgba(255,255,255,0.08)", color: "#64748b" }}>
        <p>© 2026 LangChain-KR (TeddyNote). All rights reserved.</p>
        <p style={{ marginTop: "0.5rem", fontSize: "0.8rem" }}>본 페이지는 스타팅 멤버 및 고객 제안을 위한 프로토타입 소개용 랜딩페이지입니다.</p>
      </footer>
    </div>
  );
}
