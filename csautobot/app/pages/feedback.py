"""팀원·고객 피드백 모음 페이지. 조회/필터/CSV 다운로드."""
from __future__ import annotations

from datetime import datetime

import pandas as pd
import streamlit as st

from app.ui import page_header
from storage.repositories import create_feedback, list_feedback


def _render_general_form() -> None:
    st.markdown("### 자유 의견 남기기")
    st.caption("특정 검색·점검일지가 아닌 전체 서비스에 대한 의견입니다.")
    with st.form("general_feedback_form", clear_on_submit=True):
        col1, col2 = st.columns(2)
        with col1:
            role = st.selectbox("역할", ["팀원", "고객", "엔지니어", "기타"])
            reviewer = st.text_input("이름 / 소속 (선택)", "")
        with col2:
            rating = st.slider("전반 만족도 (1~5)", 1, 5, 4)
            usefulness = st.slider("업무 도움도 (1~5)", 1, 5, 4)
        comment = st.text_area(
            "의견 / 개선 제안",
            height=140,
            placeholder="어떤 기능이 추가되면 좋을지, 어떤 부분이 불편했는지 자유롭게 적어주세요.",
        )
        submitted = st.form_submit_button("의견 저장", use_container_width=True, type="primary")
    if submitted:
        create_feedback(
            target_type="general",
            target_id=None,
            role=role,
            reviewer_name=reviewer or None,
            rating=rating,
            usefulness=usefulness,
            comment=comment or None,
        )
        st.success("의견이 저장되었습니다. 감사합니다.")


def _render_summary(df: pd.DataFrame) -> None:
    if df.empty:
        return
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.metric("총 피드백 수", f"{len(df):,}")
    with c2:
        st.metric("평균 만족도", f"{df['rating'].dropna().mean():.2f}" if df["rating"].notna().any() else "-")
    with c3:
        st.metric(
            "평균 도움도",
            f"{df['usefulness'].dropna().mean():.2f}" if df["usefulness"].notna().any() else "-",
        )
    with c4:
        st.metric("참여 역할 수", df["role"].nunique())


def render() -> None:
    page_header(
        "피드백 모음",
        "팀원·고객이 남긴 모든 의견을 한곳에서 조회하고, CSV 로 내려받을 수 있습니다.",
        icon="📬",
        accent="#FF6B6B",
    )

    tab1, tab2 = st.tabs(["📊 피드백 조회", "✍️ 자유 의견 남기기"])

    with tab1:
        col_a, col_b = st.columns([2, 1])
        with col_a:
            target_type = st.selectbox(
                "대상 유형", ["(전체)", "inspection", "search", "general"]
            )
        with col_b:
            limit = st.number_input("조회 건수 상한", 10, 1000, 200, step=10)

        rows = list_feedback(
            target_type=None if target_type == "(전체)" else target_type,
            limit=int(limit),
        )

        if not rows:
            st.info("아직 저장된 피드백이 없습니다.")
        else:
            df = pd.DataFrame(rows)
            _render_summary(df)

            st.dataframe(
                df[
                    [
                        "created_at",
                        "target_type",
                        "target_id",
                        "role",
                        "reviewer_name",
                        "rating",
                        "usefulness",
                        "comment",
                    ]
                ],
                use_container_width=True,
                hide_index=True,
            )

            ts = datetime.now().strftime("%Y%m%d_%H%M%S")
            st.download_button(
                "⬇️ CSV 다운로드",
                data=df.to_csv(index=False).encode("utf-8-sig"),
                file_name=f"csautobot_feedback_{ts}.csv",
                mime="text/csv",
                use_container_width=True,
            )

    with tab2:
        _render_general_form()


if __name__ == "__main__":
    render()
