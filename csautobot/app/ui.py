"""공통 UI 헬퍼.

페이지 상단 배너(:func:`page_header`) 등 여러 페이지에서 재사용되는 위젯.
``app.theme`` 의 CSS 토큰과 함께 사용된다.
"""
from __future__ import annotations

import html

import streamlit as st

from app.theme import COLOR_MUTED, COLOR_PRIMARY, COLOR_SECONDARY, COLOR_TEXT


def page_header(
    title: str,
    caption: str | None = None,
    *,
    icon: str = "⚡",
    accent: str = COLOR_PRIMARY,
) -> None:
    """페이지 상단의 아이콘 배지 + 그라디언트 타이틀 + 캡션."""
    safe_title = html.escape(title)
    safe_icon = html.escape(icon)
    cap_html = (
        f"<div style='color:{COLOR_MUTED};font-size:14px;line-height:1.7;margin-top:10px;max-width:820px;'>"
        f"{caption}</div>"
        if caption
        else ""
    )
    st.markdown(
        f"""
        <div style="display:flex;align-items:center;gap:14px;margin:4px 0 4px 0;">
          <div style="width:44px;height:44px;border-radius:14px;
                      background:linear-gradient(135deg,{COLOR_SECONDARY} 0%, {accent} 100%);
                      display:flex;align-items:center;justify-content:center;
                      font-size:20px;color:#00141a;font-weight:800;
                      box-shadow: 0 10px 24px -12px rgba(0,242,254,0.45);">{safe_icon}</div>
          <div style="font-family:'Outfit',sans-serif;font-size:30px;font-weight:800;
                      letter-spacing:-0.02em;color:{COLOR_TEXT};line-height:1.15;">
            {safe_title}
          </div>
        </div>
        {cap_html}
        <div style='height:14px;'></div>
        """,
        unsafe_allow_html=True,
    )
