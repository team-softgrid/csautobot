"""
AS 유사 사례 검색 페이지 (기존 streamlit_app.py 로직을 페이지로 이관).
"""
from __future__ import annotations

import os
from pathlib import Path

import streamlit as st
from langchain_chroma import Chroma
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from pydantic import BaseModel, Field

from app.ui import page_header
from retrieval import load_bm25, resolve_chroma_dir, retrieve_reranked
from storage.repositories import create_feedback

BOT_DIR = Path(__file__).resolve().parents[2]


SYS = """당신은 전기차 충전기 AS(애프터서비스) 지원 도우미입니다.
반드시 제공된 [참고 사례] 안의 내용만 근거로 답합니다.
참고 사례에 없는 추측·일반론은 하지 마세요.

출력은 지정된 JSON 스키마를 따릅니다. 각 필드는 한국어로 작성합니다.
- evidence_refs: 참고 사례 출처를 `파일경로 | 시트` 형태로 짧게 나열 (최대 5개)
- top_causes: 참고 사례에 근거가 있는 경우만 최대 3개. 근거가 없으면 빈 배열
- inspection_steps: 사례에 나온 점검/조치 순서를 요약한 단계 리스트
- parts: 사례에 언급된 교체 부품이 있으면 그대로, 없으면 "사례에 명시 없음"
- confidence_note: 시스템이 제공한 신뢰도 등급(high/mid/low)에 맞는 주의 문구

면책: 최종 판단·안전·전기 작업은 반드시 담당 엔지니어가 수행해야 합니다."""


class AnswerSchema(BaseModel):
    symptom_summary: str = Field(description="유사 사례 기준 증상 요약")
    top_causes: list[str] = Field(default_factory=list, max_length=3)
    inspection_steps: list[str] = Field(default_factory=list)
    parts: str = Field(description="필요 부품 또는 사례 부재 시 안내")
    evidence_refs: list[str] = Field(default_factory=list)
    confidence_note: str = Field(description="신뢰도·주의사항")


def _get_vs(chroma_dir: Path) -> Chroma:
    emb = OpenAIEmbeddings(model="text-embedding-3-small")
    return Chroma(
        persist_directory=str(chroma_dir),
        embedding_function=emb,
        collection_name="csautobot",
    )


def _render_search_feedback(query_text: str) -> None:
    st.markdown("---")
    with st.expander("이 검색 결과에 대한 피드백 남기기"):
        with st.form("search_feedback_form", clear_on_submit=True):
            col1, col2 = st.columns(2)
            with col1:
                role = st.selectbox("역할", ["엔지니어", "팀원", "고객", "기타"])
                reviewer = st.text_input("이름(선택)", "")
            with col2:
                rating = st.slider("전반 만족도 (1~5)", 1, 5, 4)
                usefulness = st.slider("업무 도움도 (1~5)", 1, 5, 4)
            comment = st.text_area("의견 / 개선 제안", height=100)
            submitted = st.form_submit_button("피드백 저장", use_container_width=True)
        if submitted:
            create_feedback(
                target_type="search",
                target_id=query_text[:80] if query_text else None,
                role=role,
                reviewer_name=reviewer or None,
                rating=rating,
                usefulness=usefulness,
                comment=comment or None,
            )
            st.success("피드백이 저장되었습니다. 감사합니다.")


def _clean_web_content(text: str, max_len: int = 300) -> str:
    import re
    text = re.sub(r'<[^>]+>', ' ', text)
    text = re.sub(r'\{"[^}]+}', '', text)
    text = re.sub(r'[|\n\r\t]+', ' ', text)
    text = re.sub(r' {2,}', ' ', text).strip()
    if len(text) < 30:
        return ""
    return text[:max_len] + ("…" if len(text) > max_len else "")


def _run_tavily_search(query: str) -> list | str:
    try:
        from langchain_community.tools.tavily_search import TavilySearchResults
        import os
    except ImportError:
        return []

    if not os.environ.get("TAVILY_API_KEY"):
        return []

    # 한국어 기술 키워드로 검색하여 국내 기술 문서/매뉴얼 위주로 결과 확보
    technical_query = f"전기차 충전기 {query} 고장 점검 조치 수리"

    try:
        search = TavilySearchResults(max_results=5)
        res = search.invoke({"query": technical_query})
        if isinstance(res, str):
            if "401" in res or "Unauthorized" in res:
                return "Tavily API 키가 유효하지 않습니다. .env의 TAVILY_API_KEY를 확인하세요."
            return f"웹 검색 오류: {res}"
        return res
    except Exception as e:
        if "401" in str(e) or "Unauthorized" in str(e):
            return "Tavily API 키가 유효하지 않습니다. .env의 TAVILY_API_KEY를 확인하세요."
        return f"웹 검색 오류: {str(e)}"


def render() -> None:
    page_header(
        "AS 유사 사례 검색",
        "하이브리드 검색(Dense+BM25) → 임베딩 재순위 → 신뢰도 표시. "
        "csData 엑셀 인덱스를 기반으로 한 참조용 도구이며, 최종 판단은 담당 엔지니어가 수행합니다.",
        icon="🔎",
        accent="#29B6F6",
    )

    if not os.environ.get("OPENAI_API_KEY"):
        st.error("OPENAI_API_KEY 가 설정되어 있지 않습니다. `.env` 또는 환경변수로 추가하세요.")
        return

    index_dir = resolve_chroma_dir(BOT_DIR)
    if index_dir is None:
        stale = [
            x.name
            for x in BOT_DIR.glob("chroma_db*")
            if x.is_dir() and not (x / "sparse_index.pkl").is_file()
        ]
        if stale:
            st.warning(
                "`chroma_db` / `chroma_db_*` 폴더는 있으나 **BM25용 `sparse_index.pkl`이 없습니다**.\n\n"
                "프로젝트 루트에서 `poetry run python csautobot/build_index.py` 를 실행하세요.\n\n"
                f"(갱신 필요 폴더 예: {', '.join(sorted(stale)[:5])}{'…' if len(stale) > 5 else ''})"
            )
        else:
            st.warning(
                "인덱스가 없습니다. 프로젝트 루트에서 순서대로:\n"
                "`poetry run python csautobot/ingest.py`\n"
                "`poetry run python csautobot/build_index.py`"
            )
        return

    bm25 = load_bm25(index_dir)
    emb = OpenAIEmbeddings(model="text-embedding-3-small")
    vs = _get_vs(index_dir)

    q = st.text_area(
        "증상·에러·현상을 입력하세요 (예: 에러코드 23, RFID 인식 안 됨, PLC 하트비트 없음)",
        height=120,
        key="search_query",
    )
    
    st.markdown("---")
    use_web_search = st.checkbox("🌐 웹 리서치 포함 (Tavily 연동, 약 3~5초 추가 소요)", key="search_use_web", value=False)
    
    c1, c2, c3 = st.columns(3)
    with c1:
        k_hybrid = st.slider("1차 하이브리드 후보 수", 15, 50, 30)
    with c2:
        k_dense = st.slider("Dense(벡터) 상한", 20, 80, 50)
    with c3:
        k_sparse = st.slider("Sparse(BM25) 상한", 20, 80, 50)

    if st.button("유사 사례 검색 및 답변", type="primary", use_container_width=True) and q.strip():
        with st.spinner("검색·재순위·생성 중…"):
            web_results = []
            if use_web_search:
                web_results = _run_tavily_search(q.strip())

            rr = retrieve_reranked(
                q.strip(), vs, bm25, emb,
                k_dense=k_dense, k_sparse=k_sparse, k_hybrid=k_hybrid, k_final=5,
            )
            docs = rr.documents
            ctx = "\n\n---\n\n".join(d.page_content for d in docs)

            web_ctx = ""
            if web_results:
                if isinstance(web_results, str):
                    web_ctx = f"[웹 리서치 오류]\n{web_results}\n\n"
                else:
                    lines = []
                    for res in web_results:
                        if isinstance(res, dict):
                            title = res.get('title', '')
                            content = res.get('content', '')
                            lines.append(f"- [{title}] {content}")
                    if lines:
                        web_ctx = "[웹 리서치 참고 자료]\n" + "\n".join(lines) + "\n\n"

            guard = ""
            if rr.level == "low":
                guard = (
                    "[운영 지침] 신뢰도 등급: low. 근거가 약할 수 있음을 사용자에게 명확히 알리고, "
                    "현장 점검·추가 데이터 확인을 권고하세요. 참고 사례 및 웹 리서치 밖의 추측은 금지입니다.\n\n"
                )
            elif rr.level == "mid":
                guard = (
                    "[운영 지침] 신뢰도 등급: mid. 답변은 보조용이며 필수 확인 사항을 빠짐없이 적으세요.\n\n"
                )

            llm = ChatOpenAI(model="gpt-4o-mini", temperature=0).with_structured_output(AnswerSchema)
            prompt = ChatPromptTemplate.from_messages(
                [
                    ("system", SYS),
                    (
                        "human",
                        guard
                        + "[시스템 신뢰도]\n"
                        + f"- score: {rr.confidence:.3f}\n"
                        + f"- level: {rr.level}\n\n"
                        + "[로컬 참고 사례]\n{context}\n\n"
                        + "{web_context}"
                        + "---\n사용자 질문:\n{question}",
                    ),
                ]
            )
            chain = prompt | llm
            structured: AnswerSchema = chain.invoke({"context": ctx, "web_context": web_ctx, "question": q.strip()})

        m1, m2, m3 = st.columns(3)
        with m1:
            st.metric("신뢰도 점수", f"{rr.confidence:.3f}")
        with m2:
            st.metric("등급", rr.level)
        with m3:
            st.metric("재순위 후보", rr.details.get("candidate_count", 0))

        st.subheader("구조화 답변")
        st.markdown(f"**증상 요약** — {structured.symptom_summary}")
        if structured.top_causes:
            st.markdown("**가능 원인 (최대 3)**")
            for i, c in enumerate(structured.top_causes, 1):
                st.markdown(f"{i}. {c}")
        if structured.inspection_steps:
            st.markdown("**점검 순서**")
            for i, s in enumerate(structured.inspection_steps, 1):
                st.markdown(f"{i}. {s}")
        st.markdown(f"**부품** — {structured.parts}")
        if structured.evidence_refs:
            st.markdown("**근거 출처**")
            for e in structured.evidence_refs:
                st.markdown(f"- `{e}`")
        st.info(structured.confidence_note)

        with st.expander("검색·재순위에 사용된 상위 청크 (로컬 DB 원문)"):
            for i, d in enumerate(docs, 1):
                st.markdown(f"**#{i}** `{d.metadata}`")
                st.text(d.page_content)

        if web_results:
            with st.expander("🌐 웹 리서치 결과 (Tavily) — AI 답변 생성에 참조됨"):
                if isinstance(web_results, str):
                    st.error(web_results)
                else:
                    shown = 0
                    for i, res in enumerate(web_results, 1):
                        if isinstance(res, dict):
                            title = res.get('title', '')
                            content = _clean_web_content(res.get('content', ''))
                            url = res.get('url', '')
                            if not content:
                                continue
                            shown += 1
                            st.markdown(f"**[{shown}] {title}**")
                            st.write(content)
                            st.caption(f"🔗 {url}")
                            st.divider()
                    if shown == 0:
                        st.info("유효한 웹 검색 결과가 없습니다.")

        _render_search_feedback(q.strip())
