"use client";

import React from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import "./globals.css";

const PAGE_ORDER = [
  { name: "📊 운영 대시보드", path: "/dashboard" },
  { name: "📝 점검일지 AI 어시스턴트", path: "/inspection" },
  { name: "🔎 AS 유사 사례 검색", path: "/search" },
  { name: "💡 AI 견적서 생성기", path: "/quotation" },
  { name: "📂 학습 데이터 관리", path: "/data-management" },
  { name: "👤 사용자 관리", path: "/admin/users" },
  { name: "📬 피드백 모음", path: "/feedback" },
];

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const pathname = usePathname();

  const isLandingPage =
    pathname === "/" ||
    pathname === "/login";

  return (
    <html lang="ko">
      <head>
        <title>CSAutobot · Next Gen EV Ops AI</title>
        <link rel="icon" href="/favicon.ico" />
      </head>
      <body>
        <div style={{ display: "flex", minHeight: "100vh" }}>
          {/* Sidebar */}
          {!isLandingPage && (
            <aside
              style={{
                width: "280px",
                background: "rgba(15, 23, 42, 0.95)",
                borderRight: "1px solid rgba(255, 255, 255, 0.08)",
                padding: "24px",
                display: "flex",
                flexDirection: "column",
                position: "fixed",
                height: "100vh",
                overflowY: "auto",
                zIndex: 50,
              }}
            >
              {/* Logo and Brand */}
              <div style={{ marginBottom: "32px" }}>
                <Link href="/" style={{ textDecoration: "none" }}>
                  <h1
                    style={{
                      fontSize: "24px",
                      fontWeight: "bold",
                      color: "#06b6d4",
                      display: "flex",
                      alignItems: "center",
                      gap: "8px",
                      margin: 0,
                    }}
                  >
                    ⚡ CSAutobot
                  </h1>
                </Link>
                <div
                  style={{
                    fontSize: "12px",
                    color: "#94a3b8",
                    marginTop: "4px",
                    letterSpacing: "0.5px",
                  }}
                >
                  Next Generation EV Ops AI
                </div>
              </div>

              {/* Navigation Menu */}
              <nav style={{ display: "flex", flexDirection: "column", gap: "10px", flex: 1 }}>
                <Link
                  href="/admin"
                  className={`nav-button ${pathname === "/admin" ? "active" : ""}`}
                  style={{
                    padding: "12px 16px",
                    borderRadius: "8px",
                    color: pathname === "/admin" ? "#ffffff" : "#94a3b8",
                    background: pathname === "/admin" ? "#06b6d4" : "transparent",
                    textDecoration: "none",
                    fontWeight: pathname === "/admin" ? "bold" : "normal",
                    transition: "all 0.2s",
                  }}
                >
                  🏠 홈
                </Link>
                
                <div
                  style={{
                    height: "1px",
                    background: "rgba(255, 255, 255, 0.08)",
                    margin: "8px 0",
                  }}
                />

                {PAGE_ORDER.map((page) => {
                  const isActive = pathname.startsWith(page.path);
                  return (
                    <Link
                      key={page.path}
                      href={page.path}
                      style={{
                        padding: "12px 16px",
                        borderRadius: "8px",
                        color: isActive ? "#ffffff" : "#94a3b8",
                        background: isActive ? "#06b6d4" : "transparent",
                        textDecoration: "none",
                        fontWeight: isActive ? "bold" : "normal",
                        transition: "all 0.2s",
                      }}
                      onMouseEnter={(e) => {
                        if (!isActive) e.currentTarget.style.color = "#ffffff";
                      }}
                      onMouseLeave={(e) => {
                        if (!isActive) e.currentTarget.style.color = "#94a3b8";
                      }}
                    >
                      {page.name}
                    </Link>
                  );
                })}
              </nav>

              {/* Logout Button */}
              <div style={{ marginTop: "16px", paddingTop: "16px", borderTop: "1px solid rgba(255, 255, 255, 0.08)" }}>
                <button
                  onClick={async () => {
                    await fetch("/api/auth/logout", { method: "POST" });
                    window.location.href = "/login";
                  }}
                  style={{
                    width: "100%",
                    padding: "10px 16px",
                    borderRadius: "8px",
                    color: "#f87171",
                    background: "transparent",
                    border: "1px solid rgba(248, 113, 113, 0.2)",
                    textAlign: "left",
                    cursor: "pointer",
                    fontSize: "14px",
                    fontWeight: "bold",
                    transition: "all 0.2s",
                  }}
                  onMouseEnter={(e) => {
                    e.currentTarget.style.background = "rgba(248, 113, 113, 0.1)";
                  }}
                  onMouseLeave={(e) => {
                    e.currentTarget.style.background = "transparent";
                  }}
                >
                  🚪 로그아웃
                </button>
              </div>

              {/* Caption */}
              <div
                style={{
                  borderTop: "1px solid rgba(255, 255, 255, 0.08)",
                  paddingTop: "16px",
                  marginTop: "24px",
                  fontSize: "11px",
                  color: "#64748b",
                  lineHeight: "1.6",
                }}
              >
                본 화면은 내부 데모·피드백 수집용입니다.
                <br />
                최종 안전 판단과 실제 점검·AS 시공은 담당 엔지니어가 수행합니다.
              </div>
            </aside>
          )}

          {/* Main Content Area */}
          <main
            style={{
              marginLeft: isLandingPage ? "0" : "280px",
              flex: 1,
              padding: isLandingPage ? "0" : "40px",
              minHeight: "100vh",
              background: "#0f172a",
              overflowY: "auto",
            }}
          >
            <div style={{ maxWidth: isLandingPage ? "none" : "1200px", margin: "0 auto" }}>{children}</div>
          </main>
        </div>
      </body>
    </html>
  );
}
