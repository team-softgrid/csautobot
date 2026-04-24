"""
점검일지 AI 어시스턴트 (MVP).

Week 3 실행계획의 Streamlit 화면.
- 설비/점검유형 입력
- 체크리스트(정상/주의/이상/N-A) + 메모
- 사진 업로드(현장 상태 확인)
- AI 초안 생성(구조화 JSON)
- 엔지니어 확정 → SQLite 저장
- 팀원·고객 피드백 수집 폼 제공
"""
from __future__ import annotations

import os
import uuid
from pathlib import Path

import streamlit as st

from app.ui import page_header
from services.inspection_service import (
    CHECKLIST_CYCLES,
    INSPECTION_TARGETS,
    CHECKLIST_PRESETS,
    CHECKLIST_STATUS_OPTIONS,
    InspectionDraft,
    default_checklist,
    generate_inspection_draft,
    preset_checklist,
)
from storage.repositories import (
    confirm_inspection_log,
    create_feedback,
    create_inspection_log,
    get_inspection_log,
    list_inspection_logs,
    update_inspection_ai_summary,
)

BOT_DIR = Path(__file__).resolve().parents[2]
UPLOADS_DIR = BOT_DIR / "uploads"


INSPECTION_TYPES = ["정기점검", "설치후점검", "고장 AS", "긴급출동", "예방점검"]
# 주기는 CHECKLIST_PRESETS 의 키와 1:1 매핑 (일간/주간/월간/분기/반기/연간/수시)
INSPECTION_CYCLES = CHECKLIST_CYCLES


def _ensure_state() -> None:
    """페이지 세션 상태 초기화."""
    if "insp_id" not in st.session_state:
        st.session_state.insp_id = f"ins-{uuid.uuid4().hex[:12]}"
    if "insp_target" not in st.session_state:
        st.session_state.insp_target = "충전기"
    if "insp_cycle" not in st.session_state:
        st.session_state.insp_cycle = "월간"
    if "insp_checklist" not in st.session_state:
        st.session_state.insp_checklist = preset_checklist(
            st.session_state.insp_target, st.session_state.insp_cycle
        )
    if "insp_photos" not in st.session_state:
        st.session_state.insp_photos = []
    if "insp_draft" not in st.session_state:
        st.session_state.insp_draft = None
    if "insp_draft_model" not in st.session_state:
        st.session_state.insp_draft_model = None
    if "insp_web_res" not in st.session_state:
        st.session_state.insp_web_res = ""

def _on_preset_change() -> None:
    """점검 대상이나 주기가 변경되면 점검 항목을 즉시 업데이트."""
    t = st.session_state.get("insp_target", "충전기")
    c = st.session_state.get("insp_cycle", "월간")
    new_list = preset_checklist(t, c)
    st.session_state.insp_checklist = new_list
    # Streamlit 위젯 캐시를 강제로 덮어씌움
    for idx, row in enumerate(new_list):
        st.session_state[f"insp_item_{idx}"] = row.get("item", "")
        st.session_state[f"insp_status_{idx}"] = row.get("status", "정상")
        st.session_state[f"insp_note_{idx}"] = row.get("note", "")

def _save_photos(uploaded_files, inspection_id: str) -> list[str]:
    """업로드된 사진을 로컬에 저장하고 경로 리스트 반환."""
    if not uploaded_files:
        return []
    target_dir = UPLOADS_DIR / inspection_id
    target_dir.mkdir(parents=True, exist_ok=True)
    saved: list[str] = []
    for f in uploaded_files:
        safe_name = f.name.replace("\\", "_").replace("/", "_")
        fp = target_dir / f"{uuid.uuid4().hex[:8]}_{safe_name}"
        fp.write_bytes(f.getbuffer())
        saved.append(str(fp))
    return saved


def _reset_state() -> None:
    for key in list(st.session_state.keys()):
        if key.startswith("insp_"):
            del st.session_state[key]
    _ensure_state()


def _render_checklist_editor() -> list[dict]:
    st.markdown("#### 점검 항목")
    st.caption(
        "각 항목의 상태를 '정상 / 주의 / 이상 / N/A' 중에서 선택하세요. "
        "'주의·이상'으로 표시한 항목은 AI 초안에서 우선적으로 반영됩니다."
    )

    checklist = st.session_state.insp_checklist
    new_checklist: list[dict] = []
    for idx, row in enumerate(checklist):
        c1, c2, c3, c4 = st.columns([4, 2, 5, 1])
        with c1:
            item_name = st.text_input(
                f"항목 {idx + 1}",
                value=row.get("item", ""),
                key=f"insp_item_{idx}",
                label_visibility="collapsed",
            )
        with c2:
            status = st.selectbox(
                "상태",
                CHECKLIST_STATUS_OPTIONS,
                index=CHECKLIST_STATUS_OPTIONS.index(row.get("status", "정상"))
                if row.get("status") in CHECKLIST_STATUS_OPTIONS
                else 0,
                key=f"insp_status_{idx}",
                label_visibility="collapsed",
            )
        with c3:
            note = st.text_input(
                "메모",
                value=row.get("note", ""),
                key=f"insp_note_{idx}",
                label_visibility="collapsed",
                placeholder="관찰 내용 / 수치 / 사진 번호 등",
            )
        with c4:
            drop = st.checkbox("삭제", key=f"insp_del_{idx}")
        if not drop:
            new_checklist.append({"item": item_name, "status": status, "note": note})

    st.session_state.insp_checklist = new_checklist

    btn_c1, btn_c2 = st.columns(2)
    with btn_c1:
        if st.button("+ 항목 추가", use_container_width=True):
            st.session_state.insp_checklist.append(
                {"item": "", "status": "정상", "note": ""}
            )
            st.rerun()
    with btn_c2:
        if st.button("🔄 선택한 프리셋으로 리셋", use_container_width=True):
            _on_preset_change()
            st.rerun()

    return new_checklist


def _render_draft(draft: InspectionDraft, model_name: str, web_res: str = "") -> None:
    st.markdown("### AI 초안")
    st.caption(f"생성 모델: `{model_name}` · 최종 판단은 담당 엔지니어가 수행합니다.")

    risk = draft.overall_risk.lower()
    if "high" in risk:
        st.error(f"전반 위험도: **{draft.overall_risk}**")
    elif "mid" in risk:
        st.warning(f"전반 위험도: **{draft.overall_risk}**")
    else:
        st.success(f"전반 위험도: **{draft.overall_risk}**")

    col_a, col_b = st.columns(2)
    with col_a:
        if draft.key_findings:
            st.markdown("**핵심 관찰 사항**")
            for i, f in enumerate(draft.key_findings, 1):
                st.markdown(f"{i}. {f}")
        if draft.recommended_actions:
            st.markdown("**권장 조치 순서**")
            for i, a in enumerate(draft.recommended_actions, 1):
                st.markdown(f"{i}. {a}")
    with col_b:
        if draft.parts_to_check:
            st.markdown("**점검·교체 가능 부품**")
            for p in draft.parts_to_check:
                st.markdown(f"- {p}")
        if draft.follow_up_items:
            st.markdown("**후속 점검 항목**")
            for f in draft.follow_up_items:
                st.markdown(f"- {f}")

    st.info(f"**엔지니어 요약 메모** — {draft.inspector_note}")
    st.caption(f"⚠ {draft.safety_notice}")

    if web_res:
        with st.expander("🌐 웹 리서치 결과 (Tavily) — AI 초안 생성에 참조됨"):
            for block in web_res.split("\n\n"):
                block = block.strip()
                if not block:
                    continue
                lines = block.split("\n")
                if lines:
                    st.markdown(f"**{lines[0].strip()}**")
                for line in lines[1:]:
                    line = line.strip()
                    if line.startswith("출처:"):
                        url = line.replace("출처:", "").strip()
                        st.caption(f"🔗 {url}")
                    elif line:
                        st.write(line)
                st.divider()


def _render_feedback_form(target_id: str) -> None:
    """팀원/고객 의견 수집 폼 (AI 초안에 대한 피드백)."""
    st.markdown("---")
    st.markdown("### 팀원·고객 의견 수집")
    st.caption(
        "이 AI 초안이 실제 현장에서 쓸 만한지 평가해 주세요. "
        "개선에 직접 반영됩니다."
    )
    with st.form(f"insp_feedback_form_{target_id}", clear_on_submit=True):
        col1, col2 = st.columns(2)
        with col1:
            role = st.selectbox("역할", ["엔지니어", "팀원", "고객", "기타"])
            reviewer = st.text_input("이름 / 소속 (선택)", "")
        with col2:
            rating = st.slider("전반 만족도 (1~5)", 1, 5, 4)
            usefulness = st.slider("업무 도움도 (1~5)", 1, 5, 4)
        comment = st.text_area(
            "의견 / 개선 제안",
            height=110,
            placeholder="예: '부품 교체 순서가 실제 현장과 달라요' / '체크리스트 항목에 ○○ 추가 필요'",
        )
        submitted = st.form_submit_button("피드백 저장", use_container_width=True, type="primary")
    if submitted:
        create_feedback(
            target_type="inspection",
            target_id=target_id,
            role=role,
            reviewer_name=reviewer or None,
            rating=rating,
            usefulness=usefulness,
            comment=comment or None,
        )
        st.success("피드백이 저장되었습니다. 감사합니다.")


def _render_recent_logs() -> None:
    st.markdown("### 최근 저장된 점검일지")
    logs = list_inspection_logs(limit=20)
    if not logs:
        st.caption("아직 저장된 점검일지가 없습니다.")
        return
    import pandas as pd

    rows = [
        {
            "ID": log["inspection_id"],
            "상태": log["status"],
            "충전소": log.get("site_name") or "-",
            "충전기ID": log.get("charger_id") or "-",
            "유형": log.get("inspection_type") or "-",
            "엔지니어": log.get("engineer_name") or "-",
            "작성시각": log.get("created_at") or "-",
        }
        for log in logs
    ]
    st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)

    with st.expander("저장된 점검일지 상세 조회"):
        options = {f"{l['created_at']} · {l['inspection_id']}": l["inspection_id"] for l in logs}
        choice = st.selectbox("조회할 점검일지", list(options.keys()))
        if choice:
            log = get_inspection_log(options[choice])
            if log:
                st.json(
                    {
                        k: v
                        for k, v in log.items()
                        if k not in {"checklist_json", "photo_paths_json", "ai_summary_json"}
                    }
                )
                st.markdown("**점검 항목**")
                st.json(log.get("checklist") or [])
                st.markdown("**AI 초안**")
                st.json(log.get("ai_summary") or {})


def render() -> None:
    page_header(
        "점검일지 AI 어시스턴트",
        "점검 대상, 점검 주기, 점검 항목, 엔지니어 메모를 입력하면 AI가 위험도/조치 초안을 생성합니다. "
        "엔지니어가 확정하면 SQLite 에 저장되고, 팀원·고객 피드백도 함께 수집됩니다.",
        icon="📝",
    )

    _ensure_state()
    insp_id = st.session_state.insp_id
    st.markdown(f"**작성 중 ID**: `{insp_id}`")

    with st.expander("① 설비·점검 기본 정보", expanded=True):
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            site_name = st.text_input("충전소명", "")
            charger_id = st.text_input("충전기 ID", "")
        with col2:
            manufacturer = st.text_input("제조사", "")
            model_name = st.text_input("모델명", "")
        with col3:
            inspection_target = st.selectbox(
                "점검 대상", 
                INSPECTION_TARGETS, 
                key="insp_target",
                on_change=_on_preset_change
            )
            inspection_type = st.selectbox("점검 유형", INSPECTION_TYPES)
        with col4:
            inspection_cycle = st.selectbox(
                "점검 주기",
                INSPECTION_CYCLES,
                key="insp_cycle",
                on_change=_on_preset_change
            )
            engineer_name = st.text_input("작성 엔지니어", "")

    with st.expander("② 점검 항목", expanded=True):
        checklist = _render_checklist_editor()

    with st.expander("③ 엔지니어 메모 / 특이사항", expanded=True):
        memo_text = st.text_area(
            "메모",
            height=140,
            placeholder="예: '점검 중 팬 구동 소음 확인, 추가 분해 필요'",
            key="insp_memo",
        )

    with st.expander("④ 현장 사진 업로드 (선택)", expanded=False):
        uploaded = st.file_uploader(
            "사진을 선택하거나 드래그해서 놓으세요",
            type=["png", "jpg", "jpeg", "webp"],
            accept_multiple_files=True,
            key="insp_upload",
        )
        if uploaded:
            st.caption(f"업로드 예정 파일 {len(uploaded)}개. 'AI 초안 생성' 버튼 클릭 시 저장됩니다.")
            cols = st.columns(min(4, len(uploaded)))
            for i, f in enumerate(uploaded):
                with cols[i % len(cols)]:
                    st.image(f, caption=f.name, use_container_width=True)

    st.markdown("---")
    use_web_search = st.checkbox("🌐 웹 리서치 병행 (Tavily Search 연동, 약 3~5초 추가 소요)", value=False)
    
    act_c1, act_c2, act_c3 = st.columns([2, 1, 1])
    with act_c1:
        generate_btn = st.button(
            "⚡ AI 초안 생성",
            type="primary",
            use_container_width=True,
            disabled=not os.environ.get("OPENAI_API_KEY"),
        )
    with act_c2:
        confirm_btn = st.button(
            "✔ 확정·저장",
            use_container_width=True,
            disabled=st.session_state.insp_draft is None,
        )
    with act_c3:
        if st.button("🧹 초기화", use_container_width=True):
            _reset_state()
            st.rerun()

    if not os.environ.get("OPENAI_API_KEY"):
        st.warning("`OPENAI_API_KEY` 가 설정되지 않아 AI 초안 생성이 비활성화되어 있습니다.")

    if generate_btn:
        with st.spinner("AI 초안 생성 중…"):
            saved_paths = _save_photos(uploaded, insp_id)
            if saved_paths:
                st.session_state.insp_photos = saved_paths

            draft, used_model, web_res = generate_inspection_draft(
                site_name=site_name or None,
                charger_id=charger_id or None,
                manufacturer=manufacturer or None,
                model_name=model_name or None,
                inspection_target=inspection_target or None,
                inspection_type=inspection_type,
                inspection_cycle=inspection_cycle,
                checklist=checklist,
                memo_text=memo_text,
                photo_count=len(st.session_state.insp_photos),
                use_web_search=use_web_search,
            )
            st.session_state.insp_draft = draft
            st.session_state.insp_draft_model = used_model
            st.session_state.insp_web_res = web_res

            # draft 단계: DB 에 status='draft' 로 upsert
            existing = get_inspection_log(insp_id)
            if existing:
                update_inspection_ai_summary(insp_id, draft.model_dump(), used_model)
            else:
                create_inspection_log(
                    inspection_id=insp_id,
                    site_name=site_name or None,
                    charger_id=charger_id or None,
                    manufacturer=manufacturer or None,
                    model_name=model_name or None,
                    inspection_type=inspection_type,
                    inspection_cycle=inspection_cycle,
                    engineer_name=engineer_name or None,
                    checklist=checklist,
                    memo_text=memo_text,
                    photo_paths=st.session_state.insp_photos,
                    ai_summary=draft.model_dump(),
                    ai_model=used_model,
                    status="draft",
                )
        st.success("AI 초안이 생성되었습니다. 아래에서 확인 후 필요시 확정하세요.")

    if st.session_state.insp_draft:
        _render_draft(st.session_state.insp_draft, st.session_state.insp_draft_model or "-", st.session_state.insp_web_res)

        if confirm_btn:
            # 확정 저장(없다면 생성) — 이전에 draft 로 저장된 건 상태만 변경
            existing = get_inspection_log(insp_id)
            if not existing:
                create_inspection_log(
                    inspection_id=insp_id,
                    site_name=site_name or None,
                    charger_id=charger_id or None,
                    manufacturer=manufacturer or None,
                    model_name=model_name or None,
                    inspection_type=inspection_type,
                    inspection_cycle=inspection_cycle,
                    engineer_name=engineer_name or None,
                    checklist=checklist,
                    memo_text=memo_text,
                    photo_paths=st.session_state.insp_photos,
                    ai_summary=st.session_state.insp_draft.model_dump(),
                    ai_model=st.session_state.insp_draft_model,
                    status="confirmed",
                )
            else:
                confirm_inspection_log(insp_id)
            st.success(f"점검일지 `{insp_id}` 가 확정 저장되었습니다.")

        _render_feedback_form(insp_id)

    st.markdown("---")
    _render_recent_logs()


if __name__ == "__main__":
    # 단독 실행 대비 (테스트용)
    render()
