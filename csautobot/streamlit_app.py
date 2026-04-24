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
from app.pages import data_management as data_management_page  # noqa: E402
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
DATA_KEY = "📂 학습 데이터 관리"

PAGE_ORDER = [DASH_KEY, INSP_KEY, SEARCH_KEY, DATA_KEY]


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
        dashboard_page.render(on_navigate=_set_page)
    elif key == FEEDBACK_KEY:
        feedback_page.render()
    elif key == DATA_KEY:
        data_management_page.render()
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

    # 로고 클릭 시 /?page=home 파라미터가 들어올 경우 홈으로 강제 라우팅
    if hasattr(st, "query_params") and "page" in st.query_params:
        if st.query_params["page"] == "home":
            st.session_state["csa_page"] = HOME_KEY
            st.query_params.clear()

    with st.sidebar:
        render_sidebar_brand()
        current = st.session_state["csa_page"]
        
        if current != HOME_KEY:
            st.markdown("<div style='margin-bottom: 10px;'></div>", unsafe_allow_html=True)
            
            for page in PAGE_ORDER:
                is_active = (page == current)
                # 선택된 메뉴는 primary 스타일로 강조
                btn_type = "primary" if is_active else "secondary"
                
                if st.button(page, key=f"nav_{page}", use_container_width=True, type=btn_type):
                    if current != page:
                        st.session_state["csa_page"] = page
                        st.rerun()

        st.markdown("---")
        st.caption(
            "본 화면은 내부 데모·피드백 수집용입니다.\n"
            "최종 안전 판단과 실제 점검·AS 시공은 담당 엔지니어가 수행합니다."
        )

    _render_selected_page(st.session_state["csa_page"])


if __name__ == "__main__":
    main()
