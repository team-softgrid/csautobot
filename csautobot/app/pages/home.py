"""csautobot 소개용 랜딩 페이지.

참조 ``prototype.html`` 의 섹션 구조(Hero → KPI → Workflow → Architecture → Features)를
Streamlit 환경에서 재현한다. CTA 는 사이드바 라우팅 상태를 바꿔 내부 페이지로 이동한다.
"""
from __future__ import annotations

import html
from typing import Callable

import streamlit as st

from app.theme import BRAND_NAME
from storage.repositories import list_feedback, list_inspection_logs


# ---------- Hero ----------
def _hero(on_navigate: Callable[[str], None] | None = None) -> None:
    st.markdown(
        """
        <div class="csa-hero">
          <div class="orb" style="top: 8%; right: 10%;"></div>
          <div class="orb" style="bottom: 4%; left: 8%; background: var(--accent); opacity: 0.18;"></div>

          <span class="badge">Next Generation EV Ops AI</span>
          <h1>EV Infrastructure<br/>Technical Copilot</h1>
          <p class="lead">
            전기차 충전소 <b>정기점검·고장 AS·민원 대응</b>을 하나의 워크플로로 묶습니다.
            현장 체크리스트와 사진·메모를 입력하면 AI가 위험도와 권장 조치를 구조화해 초안으로 먼저 작성하고,
            과거 AS 데이터는 하이브리드 RAG 로 즉시 근거와 함께 제시합니다.
          </p>
          <div class="chip-row">
            <span class="csa-chip"><span class="dot"></span> 점검일지 AI 초안</span>
            <span class="csa-chip"><span class="dot"></span> AS RAG 검색</span>
            <span class="csa-chip"><span class="dot"></span> 위험도 자동 판정</span>
            <span class="csa-chip"><span class="dot"></span> 엔지니어 확정 워크플로</span>
            <span class="csa-chip"><span class="dot"></span> 운영 대시보드</span>
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    if on_navigate:
        st.markdown("<div style='text-align: center; margin-top: -10px; margin-bottom: 40px;'>", unsafe_allow_html=True)
        c1, c2, c3 = st.columns([1, 1, 1])
        with c2:
            if st.button("🚀 시작하기 (운영 대시보드 입장)", use_container_width=True, type="primary", key="hero_start"):
                on_navigate("📊 운영 대시보드")
                st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)


# ---------- KPI ----------
def _kpi_card(label: str, value: str, trend: str | None = None, kind: str = "up") -> str:
    trend_html = ""
    if trend:
        cls = "up" if kind == "up" else "down"
        trend_html = f'<div class="trend"><span class="{cls}">{html.escape(trend)}</span></div>'
    return f"""
    <div class="csa-kpi-card">
      <div class="label">{html.escape(label)}</div>
      <div class="value">{html.escape(value)}</div>
      {trend_html}
    </div>
    """


def _kpi_section() -> None:
    logs = list_inspection_logs(limit=1000)
    feedbacks = list_feedback(limit=1000)

    total = len(logs)
    confirmed = sum(1 for l in logs if (l.get("status") or "") == "confirmed")
    high = sum(
        1
        for l in logs
        if "high" in str((l.get("ai_summary") or {}).get("overall_risk", "")).lower()
    )
    ratings = [f.get("rating") for f in feedbacks if f.get("rating") is not None]
    avg_rating = (sum(ratings) / len(ratings)) if ratings else None

    confirm_rate = (confirmed / total * 100) if total else 0.0

    cards_html = "".join(
        [
            _kpi_card("누적 점검일지", f"{total:,}"),
            _kpi_card("엔지니어 확정률", f"{confirm_rate:.0f}%", f"{confirmed:,}건 확정"),
            _kpi_card("고위험 탐지", f"{high:,}", "자동 에스컬레이션"),
            _kpi_card(
                "피드백 만족도",
                f"{avg_rating:.2f}" if avg_rating is not None else "—",
                "1~5점 평균",
            ),
        ]
    )

    st.markdown(
        f"""
        <div class="csa-section-title">
          <div class="eyebrow">Real-time Intelligence</div>
          <h2>현장에서 쌓이는 데이터</h2>
          <p>로컬 SQLite 에 축적된 점검·피드백을 실시간으로 집계합니다.</p>
        </div>
        <div class="csa-kpi-grid">{cards_html}</div>
        """,
        unsafe_allow_html=True,
    )


# ---------- Workflow ----------
def _workflow_section() -> None:
    st.markdown(
        """
        <div class="csa-section-title">
          <div class="eyebrow">Inspection Workflow</div>
          <h2>3단계로 끝나는 점검일지</h2>
          <p>입력 → AI 초안 → 엔지니어 확정. 모든 단계가 한 화면에서 끝납니다.</p>
        </div>

        <div class="csa-feature-grid">
          <div class="csa-feature-card">
            <div class="icon">1</div>
            <div>
              <h4>입력</h4>
              <p>충전소·충전기 정보 + 주기별 표준 체크리스트 + 현장 메모·사진. 일간/주간/월간/분기/반기/연간/수시 프리셋을 즉시 불러올 수 있습니다.</p>
            </div>
          </div>
          <div class="csa-feature-card">
            <div class="icon">2</div>
            <div>
              <h4>AI 초안</h4>
              <p>위험도(low/mid/high), 핵심 관찰, 권장 조치 순서, 교체 가능 부품, 후속 점검 항목을 JSON 스키마로 구조화 생성합니다.</p>
            </div>
          </div>
          <div class="csa-feature-card">
            <div class="icon">3</div>
            <div>
              <h4>확정 & 축적</h4>
              <p>엔지니어가 확정하면 SQLite 에 저장되어 대시보드·RAG 근거로 누적됩니다. 팀원·고객 피드백도 같은 화면에서 수집합니다.</p>
            </div>
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


# ---------- Architecture ----------
def _architecture_section() -> None:
    st.markdown(
        """
        <div class="csa-section-title">
          <div class="eyebrow">System Architecture</div>
          <h2>Secure RAG Pipeline</h2>
          <p>민감한 AS 데이터를 외부로 보내지 않도록 로컬 파일·DB 우선 구조를 유지합니다.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    left, right = st.columns([1, 1])
    with left:
        st.markdown(
            """
            <div class="csa-arch-card">
              <div class="csa-arch-step">
                <div class="num">1</div>
                <div>
                  <div class="title">Hybrid Retrieval</div>
                  <div class="desc">Dense(OpenAI Embedding) + Sparse(BM25) 동시 검색으로 exact keyword 와 의미 유사도를 함께 활용합니다.</div>
                </div>
              </div>
              <div class="csa-arch-step">
                <div class="num">2</div>
                <div>
                  <div class="title">Embedding Rerank</div>
                  <div class="desc">1차 후보군(30~50개) 을 임베딩 기반 코사인 유사도로 재순위 → 상위 5개만 답변에 반영합니다.</div>
                </div>
              </div>
              <div class="csa-arch-step">
                <div class="num">3</div>
                <div>
                  <div class="title">Confidence Scoring</div>
                  <div class="desc">검색 점수 분포를 기반으로 high/mid/low 신뢰도 등급을 산출하고, low 일 때는 답변에 강한 주의 문구를 강제합니다.</div>
                </div>
              </div>
              <div class="csa-arch-step">
                <div class="num">4</div>
                <div>
                  <div class="title">Structured Generation</div>
                  <div class="desc">LLM 에 Pydantic JSON 스키마를 강제하여 증상/원인/점검순서/부품/근거출처 필드를 놓치지 않게 생성합니다.</div>
                </div>
              </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with right:
        st.markdown(
            """
            <div style="padding: 10px 4px 0 4px;">
              <h3 style="margin: 0 0 10px 0; font-size: 22px;">로컬 우선 · 엔지니어 최종 확정</h3>
              <p style="color: var(--text-dim); margin: 0 0 14px 0; line-height: 1.7;">
                점검·AS 데이터는 <b>csautobot/storage/</b> 의 SQLite 와 <b>csautobot/chroma_db_*/</b> 의
                로컬 벡터 인덱스에만 저장됩니다. AI 초안은 언제나 <b>보조 판단</b>이며, 최종 안전 판단과 실제 점검·AS 시공은
                담당 엔지니어가 수행합니다.
              </p>
              <div class="csa-tech-tags">
                <span class="csa-tech-tag accent">LangChain</span>
                <span class="csa-tech-tag">Chroma</span>
                <span class="csa-tech-tag">BM25</span>
                <span class="csa-tech-tag">OpenAI Embedding</span>
                <span class="csa-tech-tag">GPT-4o-mini</span>
                <span class="csa-tech-tag">SQLite (WAL)</span>
                <span class="csa-tech-tag">Streamlit</span>
                <span class="csa-tech-tag">Pydantic</span>
              </div>
            </div>
            """,
            unsafe_allow_html=True,
        )


# ---------- Feature highlights ----------
def _features_section() -> None:
    st.markdown(
        """
        <div class="csa-section-title">
          <div class="eyebrow">Key Advantages</div>
          <h2>왜 csautobot 인가</h2>
          <p>단순 Q&amp;A 봇이 아닌 <b>현장 점검·AS 전용</b>으로 설계된 도메인 코파일럿입니다.</p>
        </div>

        <div class="csa-feature-grid">

          <div class="csa-feature-card">
            <div class="icon">🛡</div>
            <div>
              <h4>데이터 보안성</h4>
              <p>점검일지·AS 원본은 로컬 SQLite/Chroma 에만 저장됩니다. 외부 학습이나 벤더 백엔드로 전송되지 않습니다.</p>
            </div>
          </div>

          <div class="csa-feature-card">
            <div class="icon">⚡</div>
            <div>
              <h4>실시간 정확도</h4>
              <p>새 엑셀 파일만 드롭하면 ingest·index 명령 한 번으로 반영. 신규 장애 유형에도 즉각 대응 가능합니다.</p>
            </div>
          </div>

          <div class="csa-feature-card">
            <div class="icon">📊</div>
            <div>
              <h4>통합 대시보드</h4>
              <p>점검 추이, 유형·주기·위험도 분포, 설비별 Top-N, 피드백 요약을 한 화면에서 확인합니다.</p>
            </div>
          </div>

          <div class="csa-feature-card">
            <div class="icon">🧭</div>
            <div>
              <h4>엔지니어 권한 우선</h4>
              <p>AI 초안은 엔지니어 검토 전까지 draft 상태로만 존재합니다. 확정(confirmed) 전까지는 KPI/RAG 근거에서 분리 처리됩니다.</p>
            </div>
          </div>

          <div class="csa-feature-card">
            <div class="icon">🔎</div>
            <div>
              <h4>근거 기반 답변</h4>
              <p>모든 RAG 답변은 참조 사례(파일경로 | 시트) 를 함께 반환합니다. 추측/일반론은 프롬프트로 차단합니다.</p>
            </div>
          </div>

          <div class="csa-feature-card">
            <div class="icon">📬</div>
            <div>
              <h4>팀·고객 피드백 루프</h4>
              <p>검색/점검/전반 서비스 각각에 피드백 폼을 내장. CSV 로 내려 받아 다음 개선 스프린트에 바로 반영합니다.</p>
            </div>
          </div>

        </div>
        """,
        unsafe_allow_html=True,
    )


# ---------- Footer ----------
def _footer_note() -> None:
    st.markdown(
        f"""
        <div class="csa-footer-note">
          ⚠ 본 화면은 내부 데모·피드백 수집용 MVP 입니다. 모든 AI 초안은 보조 판단이며,
          <b>최종 안전 판단과 실제 점검·AS 시공은 담당 엔지니어</b>가 수행합니다. <br/>
          © {html.escape(BRAND_NAME)} · Local-first EV Ops Copilot
        </div>
        """,
        unsafe_allow_html=True,
    )


# ---------- public entry ----------
def render(on_navigate: Callable[[str], None] | None = None) -> None:
    """홈(랜딩) 페이지 렌더링."""
    # 랜딩 페이지에서는 사이드바를 완전히 숨김
    st.markdown("""
        <style>
            section[data-testid="stSidebar"] { display: none !important; }
            button[data-testid="collapsedControl"] { display: none !important; }
        </style>
    """, unsafe_allow_html=True)
    
    _hero(on_navigate)
    _kpi_section()
    _workflow_section()
    _architecture_section()
    _features_section()
    _footer_note()


if __name__ == "__main__":
    render()
