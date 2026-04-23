"""
csautobot — 통합 Streamlit 진입점 (멀티페이지).

실행:
  cd 프로젝트 루트
  poetry run streamlit run csautobot/streamlit_app.py

페이지:
  0. 🏠 홈 (랜딩·소개)
  1. 📝 점검일지 AI 어시스턴트
  2. 🔎 AS 유사 사례 검색
  3. 📊 운영 대시보드
  4. 📬 피드백 모음

사전(검색 봇만 해당):
  poetry run python csautobot/ingest.py
  poetry run python csautobot/build_index.py
"""
from __future__ import annotations

import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent

try:
    from dotenv import load_dotenv

    sys.path.insert(0, str(HERE))
    from paths import repo_root  # noqa: E402

    load_dotenv(repo_root(HERE) / ".env")
except ImportError:
    pass

if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))

import streamlit as st  # noqa: E402

from app.pages import dashboard as dashboard_page  # noqa: E402
from app.pages import feedback as feedback_page  # noqa: E402
from app.pages import home as home_page  # noqa: E402
from app.pages import inspection_log as inspection_page  # noqa: E402
from app.pages import search as search_page  # noqa: E402
from app.theme import (  # noqa: E402
    BRAND_NAME,
    BRAND_TAGLINE,
    inject_global_css,
    render_sidebar_brand,
)
from storage.db import init_db  # noqa: E402

HOME_KEY = "🏠 홈"
INSP_KEY = "📝 점검일지 AI 어시스턴트"
SEARCH_KEY = "🔎 AS 유사 사례 검색"
DASH_KEY = "📊 운영 대시보드"
FEEDBACK_KEY = "📬 피드백 모음"

PAGE_ORDER = [HOME_KEY, INSP_KEY, SEARCH_KEY, DASH_KEY, FEEDBACK_KEY]


def _set_page(key: str) -> None:
    st.session_state["csa_page"] = key


def _render_selected_page(key: str) -> None:
    if key == HOME_KEY:
        home_page.render(on_navigate=_set_page)
    elif key == INSP_KEY:
        inspection_page.render()
    elif key == SEARCH_KEY:
        search_page.render()
    elif key == DASH_KEY:
        dashboard_page.render()
    elif key == FEEDBACK_KEY:
        feedback_page.render()
    else:
        home_page.render(on_navigate=_set_page)


def main() -> None:
    st.set_page_config(
        page_title=f"{BRAND_NAME} · {BRAND_TAGLINE}",
        page_icon="⚡",
        layout="wide",
        initial_sidebar_state="expanded",
    )

    inject_global_css()
    init_db()

    if "csa_page" not in st.session_state:
        st.session_state["csa_page"] = HOME_KEY

    with st.sidebar:
        render_sidebar_brand()
        current = st.session_state["csa_page"]
        try:
            idx = PAGE_ORDER.index(current)
        except ValueError:
            idx = 0
        page_key = st.radio(
            "메뉴",
            PAGE_ORDER,
            index=idx,
            label_visibility="collapsed",
            key="csa_nav_radio",
        )
        if page_key != current:
            st.session_state["csa_page"] = page_key
            current = page_key

        st.markdown("---")
        st.caption(
            "본 화면은 내부 데모·피드백 수집용입니다.\n"
            "최종 안전 판단과 실제 점검·AS 시공은 담당 엔지니어가 수행합니다."
        )

    _render_selected_page(st.session_state["csa_page"])


if __name__ == "__main__":
    main()
