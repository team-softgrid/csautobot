"""운영 대시보드.

기간 필터·요약 메트릭·분포/추이 차트·피드백 요약을 한 화면에.
차트는 Altair 로 브랜드 컬러(시안/스카이/핑크)를 입혀 prototype.html 톤과 맞춘다.
"""
from __future__ import annotations

from datetime import date, datetime, timedelta
from typing import Any, Callable

import altair as alt
import pandas as pd
import streamlit as st

from app.theme import (
    COLOR_ACCENT,
    COLOR_DANGER,
    COLOR_MUTED,
    COLOR_PRIMARY,
    COLOR_SECONDARY,
    COLOR_SUCCESS,
    COLOR_WARN,
)
from app.ui import page_header
from storage.repositories import list_feedback, list_inspection_logs


# ----- Altair 공용 테마 적용 -----
def _apply_alt_theme() -> None:
    alt.themes.register(
        "csautobot",
        lambda: {
            "config": {
                "background": None,
                "view": {"stroke": "transparent"},
                "axis": {
                    "labelColor": COLOR_MUTED,
                    "titleColor": COLOR_MUTED,
                    "gridColor": "rgba(255,255,255,0.06)",
                    "domainColor": "rgba(255,255,255,0.12)",
                    "tickColor": "rgba(255,255,255,0.12)",
                    "labelFont": "Inter",
                    "titleFont": "Outfit",
                    "labelFontSize": 11,
                    "titleFontSize": 12,
                },
                "legend": {
                    "labelColor": COLOR_MUTED,
                    "titleColor": COLOR_MUTED,
                    "labelFont": "Inter",
                    "titleFont": "Outfit",
                },
                "range": {
                    "category": [
                        COLOR_PRIMARY,
                        COLOR_SECONDARY,
                        COLOR_ACCENT,
                        COLOR_SUCCESS,
                        COLOR_WARN,
                        COLOR_DANGER,
                    ]
                },
            }
        },
    )
    alt.themes.enable("csautobot")


RISK_ORDER = {"low": 0, "mid": 1, "high": 2}


def _risk_key(v: Any) -> str:
    s = str(v or "").lower()
    for k in ("high", "mid", "low"):
        if k in s:
            return k
    return "low"


def _parse_ts(v: Any) -> datetime | None:
    """ISO8601 문자열을 naive datetime 으로 파싱한다.

    DB 에 저장된 ``created_at`` 이 tz-aware(UTC+09:00) 인 경우가 있어,
    pandas 비교에서 tz 혼용으로 터지지 않도록 tzinfo 를 제거해 정규화한다.
    """
    if not v:
        return None
    try:
        dt = datetime.fromisoformat(str(v))
    except ValueError:
        try:
            dt = datetime.strptime(str(v)[:19], "%Y-%m-%dT%H:%M:%S")
        except ValueError:
            return None
    if dt.tzinfo is not None:
        dt = dt.replace(tzinfo=None)
    return dt


def _load_frames() -> tuple[pd.DataFrame, pd.DataFrame]:
    logs = list_inspection_logs(limit=1000)
    feedbacks = list_feedback(limit=1000)

    if logs:
        rows = []
        for log in logs:
            ai = log.get("ai_summary") or {}
            rows.append(
                {
                    "inspection_id": log.get("inspection_id"),
                    "created_at": _parse_ts(log.get("created_at")),
                    "status": log.get("status") or "draft",
                    "inspection_type": log.get("inspection_type") or "-",
                    "inspection_cycle": log.get("inspection_cycle") or "-",
                    "site_name": log.get("site_name") or "-",
                    "charger_id": log.get("charger_id") or "-",
                    "manufacturer": log.get("manufacturer") or "-",
                    "engineer_name": log.get("engineer_name") or "-",
                    "overall_risk": _risk_key(ai.get("overall_risk") if isinstance(ai, dict) else None),
                    "photo_count": len(log.get("photo_paths") or []),
                    "checklist_count": len(log.get("checklist") or []),
                }
            )
        ins_df = pd.DataFrame(rows)
    else:
        ins_df = pd.DataFrame(
            columns=[
                "inspection_id", "created_at", "status", "inspection_type", "inspection_cycle",
                "site_name", "charger_id", "manufacturer", "engineer_name",
                "overall_risk", "photo_count", "checklist_count",
            ]
        )

    if feedbacks:
        fb_df = pd.DataFrame(feedbacks)
        fb_df["created_at"] = fb_df["created_at"].map(_parse_ts)
    else:
        fb_df = pd.DataFrame(
            columns=[
                "feedback_id", "target_type", "target_id", "role",
                "reviewer_name", "rating", "usefulness", "comment", "created_at",
            ]
        )

    return ins_df, fb_df


def _date_filter(df: pd.DataFrame, start: date, end: date, col: str = "created_at") -> pd.DataFrame:
    if df.empty or col not in df.columns:
        return df
    mask = df[col].notna()
    out = df[mask].copy()
    # tz-aware 값이 남아 있으면 tz 를 떼어 네이티브로 통일
    series = pd.to_datetime(out[col], errors="coerce")
    if getattr(series.dt, "tz", None) is not None:
        series = series.dt.tz_localize(None)
    out[col] = series
    s = pd.Timestamp(start)
    e = pd.Timestamp(end) + pd.Timedelta(days=1)
    return out[(out[col] >= s) & (out[col] < e)]


def _metric_block(ins_df: pd.DataFrame, fb_df: pd.DataFrame) -> None:
    total = len(ins_df)
    confirmed = int((ins_df["status"] == "confirmed").sum()) if total else 0
    conf_rate = (confirmed / total * 100) if total else 0.0
    high_risk = int((ins_df["overall_risk"] == "high").sum()) if total else 0

    rating_mean = float(fb_df["rating"].dropna().mean()) if not fb_df.empty and fb_df["rating"].notna().any() else None
    usefulness_mean = (
        float(fb_df["usefulness"].dropna().mean())
        if not fb_df.empty and fb_df["usefulness"].notna().any()
        else None
    )

    c1, c2, c3, c4, c5 = st.columns(5)
    with c1:
        st.metric("점검 건수", f"{total:,}")
    with c2:
        st.metric("확정 건수", f"{confirmed:,}", f"{conf_rate:.0f}%")
    with c3:
        st.metric("고위험(high) 건수", f"{high_risk:,}")
    with c4:
        st.metric("피드백 만족도", f"{rating_mean:.2f}" if rating_mean is not None else "-")
    with c5:
        st.metric("업무 도움도", f"{usefulness_mean:.2f}" if usefulness_mean is not None else "-")


def _chart_inspection_trend(ins_df: pd.DataFrame) -> None:
    st.markdown("#### 일자별 점검 건수")
    if ins_df.empty or ins_df["created_at"].isna().all():
        st.caption("표시할 점검 데이터가 없습니다.")
        return
    daily = (
        ins_df.dropna(subset=["created_at"])
        .assign(date=lambda d: d["created_at"].dt.date)
        .groupby("date")
        .size()
        .rename("count")
        .reset_index()
    )
    base = alt.Chart(daily).encode(
        x=alt.X("date:T", title=None),
        y=alt.Y("count:Q", title="건수"),
        tooltip=["date:T", "count:Q"],
    )
    area = base.mark_area(
        line={"color": COLOR_PRIMARY, "strokeWidth": 2.5},
        color=alt.Gradient(
            gradient="linear",
            stops=[
                alt.GradientStop(color=COLOR_PRIMARY, offset=0),
                alt.GradientStop(color="rgba(0,242,254,0.02)", offset=1),
            ],
            x1=1, x2=1, y1=1, y2=0,
        ),
        interpolate="monotone",
    )
    points = base.mark_circle(color=COLOR_PRIMARY, size=90, stroke="#ffffff", strokeWidth=2)
    st.altair_chart((area + points).properties(height=230), use_container_width=True)


def _bar(df: pd.DataFrame, x_field: str, color: str, height: int = 240) -> alt.Chart:
    return (
        alt.Chart(df)
        .mark_bar(
            cornerRadiusTopLeft=6,
            cornerRadiusTopRight=6,
            color=color,
            opacity=0.72,
            stroke=color,
            strokeWidth=1.5,
        )
        .encode(
            x=alt.X(f"{x_field}:N", sort="-y", title=None),
            y=alt.Y("count:Q", title="건수"),
            tooltip=[f"{x_field}:N", "count:Q"],
        )
        .properties(height=height)
    )


def _chart_type_cycle(ins_df: pd.DataFrame) -> None:
    c1, c2 = st.columns(2)
    with c1:
        st.markdown("#### 점검 유형 분포")
        if ins_df.empty:
            st.caption("데이터 없음")
        else:
            df = ins_df["inspection_type"].value_counts().reset_index()
            df.columns = ["inspection_type", "count"]
            st.altair_chart(_bar(df, "inspection_type", COLOR_SECONDARY), use_container_width=True)
    with c2:
        st.markdown("#### 점검 주기 분포")
        if ins_df.empty:
            st.caption("데이터 없음")
        else:
            df = ins_df["inspection_cycle"].value_counts().reset_index()
            df.columns = ["inspection_cycle", "count"]
            st.altair_chart(_bar(df, "inspection_cycle", COLOR_ACCENT), use_container_width=True)


def _chart_risk_distribution(ins_df: pd.DataFrame) -> None:
    st.markdown("#### AI 위험도 분포")
    if ins_df.empty:
        st.caption("데이터 없음")
        return
    order = ["low", "mid", "high"]
    vc = ins_df["overall_risk"].value_counts().reindex(order).fillna(0).astype(int)
    total = int(vc.sum())
    cols = st.columns(3)
    labels = {"low": "low", "mid": "mid", "high": "high"}
    for i, level in enumerate(order):
        with cols[i]:
            pct = (vc[level] / total * 100) if total else 0.0
            st.metric(labels[level], f"{int(vc[level])}", f"{pct:.0f}%")
    df = vc.reset_index()
    df.columns = ["level", "count"]
    color_map = alt.Scale(
        domain=["low", "mid", "high"],
        range=[COLOR_SUCCESS, COLOR_WARN, COLOR_DANGER],
    )
    chart = (
        alt.Chart(df)
        .mark_bar(
            cornerRadiusTopLeft=6,
            cornerRadiusTopRight=6,
            opacity=0.78,
            strokeWidth=1.5,
        )
        .encode(
            x=alt.X("level:N", sort=order, title=None),
            y=alt.Y("count:Q", title="건수"),
            color=alt.Color("level:N", scale=color_map, legend=None),
            stroke=alt.Color("level:N", scale=color_map, legend=None),
            tooltip=["level:N", "count:Q"],
        )
        .properties(height=200)
    )
    st.altair_chart(chart, use_container_width=True)


def _chart_top_chargers(ins_df: pd.DataFrame) -> None:
    st.markdown("#### 설비별 점검 횟수 Top 10")
    if ins_df.empty:
        st.caption("데이터 없음")
        return
    s = (
        ins_df[ins_df["charger_id"] != "-"]
        .groupby("charger_id")
        .size()
        .sort_values(ascending=False)
        .head(10)
        .reset_index()
    )
    s.columns = ["charger_id", "count"]
    if s.empty:
        st.caption("충전기 ID 가 입력된 점검이 없습니다.")
        return
    chart = (
        alt.Chart(s)
        .mark_bar(
            cornerRadiusTopLeft=6,
            cornerRadiusTopRight=6,
            color=COLOR_PRIMARY,
            opacity=0.72,
            stroke=COLOR_PRIMARY,
            strokeWidth=1.5,
        )
        .encode(
            y=alt.Y("charger_id:N", sort="-x", title=None),
            x=alt.X("count:Q", title="점검 횟수"),
            tooltip=["charger_id:N", "count:Q"],
        )
        .properties(height=320)
    )
    st.altair_chart(chart, use_container_width=True)


def _recent_feedback(fb_df: pd.DataFrame) -> None:
    st.markdown("#### 최근 피드백")
    if fb_df.empty:
        st.caption("피드백이 아직 없습니다.")
        return
    show = fb_df.sort_values("created_at", ascending=False).head(10)[
        ["created_at", "target_type", "role", "reviewer_name", "rating", "usefulness", "comment"]
    ]
    st.dataframe(show, use_container_width=True, hide_index=True)


def render(on_navigate: Callable[[str], None] | None = None) -> None:
    page_header(
        "운영 대시보드",
        "점검일지 저장·확정·AI 위험도와 피드백을 한 화면에서 확인합니다. "
        "데이터는 SQLite 에 저장된 항목만 집계됩니다.",
        icon="📊",
        accent=COLOR_SECONDARY,
    )

    _apply_alt_theme()

    ins_all, fb_all = _load_frames()

    today = date.today()
    default_start = today - timedelta(days=30)
    col_a, col_b, col_c = st.columns([2, 2, 1])
    with col_a:
        start_d = st.date_input("시작일", default_start)
    with col_b:
        end_d = st.date_input("종료일", today)
    with col_c:
        st.write("")
        if st.button("🔄 새로고침", use_container_width=True):
            st.rerun()

    if isinstance(start_d, tuple):
        start_d = start_d[0]
    if isinstance(end_d, tuple):
        end_d = end_d[0]

    ins_df = _date_filter(ins_all, start_d, end_d, "created_at")
    fb_df = _date_filter(fb_all, start_d, end_d, "created_at")

    st.markdown("---")
    _metric_block(ins_df, fb_df)
    st.markdown("---")

    _chart_inspection_trend(ins_df)
    st.markdown("")
    _chart_type_cycle(ins_df)
    st.markdown("")
    _chart_risk_distribution(ins_df)
    st.markdown("")
    _chart_top_chargers(ins_df)
    st.markdown("---")
    _recent_feedback(fb_df)

    with st.expander("원시 데이터 (이 기간 점검일지)"):
        if ins_df.empty:
            st.caption("데이터 없음")
        else:
            st.dataframe(ins_df, use_container_width=True, hide_index=True)


if __name__ == "__main__":
    render()
