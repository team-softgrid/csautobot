"""
증상/에러 설명을 입력하면 csData 기반 유사 AS 사례와 조치 요약을 보여줍니다.

실행:
  cd 프로젝트 루트
  poetry run streamlit run scripts/csdata_as_bot/streamlit_app.py
  (앱이 프로젝트 루트의 .env 에서 OPENAI_API_KEY 를 읽습니다.)

사전:
  poetry run python scripts/csdata_as_bot/ingest.py
  poetry run python scripts/csdata_as_bot/build_index.py

의존성: langchain-openai 0.3.14+ 는 langchain-core >= 0.3.58 과 맞춰야 합니다.
  (ImportError: convert_to_openai_data_block … 발생 시)
  poetry run pip install "langchain-core>=0.3.58,<0.4"
  (text-splitters는 PyPI에 0.3.11까지; 필요 시) poetry run pip install "langchain-text-splitters>=0.3.8,<=0.3.11"
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
# Streamlit은 .env를 자동으로 읽지 않음 → 프로젝트 루트 .env 로드
try:
    from dotenv import load_dotenv

    load_dotenv(HERE.parents[1] / ".env")
except ImportError:
    pass

if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))

import streamlit as st
from langchain_chroma import Chroma
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from pydantic import BaseModel, Field

from retrieval import load_bm25, resolve_chroma_dir, retrieve_reranked  # noqa: E402

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
    top_causes: list[str] = Field(
        default_factory=list,
        description="가능 원인 최대 3개",
        max_length=3,
    )
    inspection_steps: list[str] = Field(default_factory=list, description="점검/조치 순서")
    parts: str = Field(description="필요 부품 또는 사례 부재 시 안내")
    evidence_refs: list[str] = Field(default_factory=list, description="근거 출처 요약")
    confidence_note: str = Field(description="신뢰도·주의사항")


def get_vectorstore(chroma_dir: Path) -> Chroma:
    emb = OpenAIEmbeddings(model="text-embedding-3-small")
    return Chroma(
        persist_directory=str(chroma_dir),
        embedding_function=emb,
        collection_name="csdata_as",
    )


def main() -> None:
    st.set_page_config(page_title="충전기 AS 증상·조치 봇", layout="wide")
    st.title("전기차 충전기 AS — 증상·조치 참조 봇")
    st.caption(
        "하이브리드 검색(Dense+BM25) → 임베딩 재순위 → 신뢰도 표시. "
        "csData 엑셀을 인덱싱한 검색형 보조 도구입니다. 법적/안전 책임은 담당자에게 있습니다."
    )

    if not os.environ.get("OPENAI_API_KEY"):
        st.error("OPENAI_API_KEY 가 설정되어 있지 않습니다. `.env` 또는 환경변수로 추가하세요.")
        return

    index_dir = resolve_chroma_dir(HERE)
    if index_dir is None:
        stale = [
            x.name
            for x in HERE.glob("chroma_db*")
            if x.is_dir() and not (x / "sparse_index.pkl").is_file()
        ]
        if stale:
            st.warning(
                "`chroma_db` / `chroma_db_*` 폴더는 있으나 **BM25용 `sparse_index.pkl`이 없습니다** "
                "(구버전 인덱스이거나 빌드가 끝나지 않았습니다).\n\n"
                "프로젝트 루트에서:\n"
                "`poetry run python scripts/csdata_as_bot/build_index.py`\n\n"
                f"(갱신 필요 폴더 예: {', '.join(sorted(stale)[:5])}{'…' if len(stale) > 5 else ''})"
            )
        else:
            st.warning(
                "인덱스가 없습니다. 프로젝트 루트에서 순서대로:\n"
                "`poetry run python scripts/csdata_as_bot/ingest.py`\n"
                "`poetry run python scripts/csdata_as_bot/build_index.py`"
            )
        return

    bm25 = load_bm25(index_dir)

    emb = OpenAIEmbeddings(model="text-embedding-3-small")
    vs = get_vectorstore(index_dir)

    q = st.text_area(
        "증상·에러·현상을 입력하세요 (예: 에러코드 23, RFID 인식 안 됨, PLC 하트비트 없음)",
        height=120,
    )
    k_hybrid = st.slider("1차 하이브리드 후보 수", 15, 50, 30)
    k_dense = st.slider("Dense(벡터) 상한", 20, 80, 50)
    k_sparse = st.slider("Sparse(BM25) 상한", 20, 80, 50)

    if st.button("유사 사례 검색 및 답변", type="primary") and q.strip():
        with st.spinner("검색·재순위·생성 중…"):
            rr = retrieve_reranked(
                q.strip(),
                vs,
                bm25,
                emb,
                k_dense=k_dense,
                k_sparse=k_sparse,
                k_hybrid=k_hybrid,
                k_final=5,
            )
            docs = rr.documents
            ctx = "\n\n---\n\n".join(d.page_content for d in docs)

            guard = ""
            if rr.level == "low":
                guard = (
                    "[운영 지침] 신뢰도 등급: low. 근거가 약할 수 있음을 사용자에게 명확히 알리고, "
                    "현장 점검·추가 데이터 확인을 권고하세요. 참고 사례 밖 추측은 금지입니다.\n\n"
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
                        + "[참고 사례]\n{context}\n\n---\n사용자 질문:\n{question}",
                    ),
                ]
            )
            chain = prompt | llm
            structured: AnswerSchema = chain.invoke({"context": ctx, "question": q.strip()})

        c1, c2, c3 = st.columns(3)
        with c1:
            st.metric("신뢰도 점수", f"{rr.confidence:.3f}")
        with c2:
            st.metric("등급", rr.level)
        with c3:
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

        with st.expander("검색·재순위에 사용된 상위 청크 (원문)"):
            for i, d in enumerate(docs, 1):
                st.markdown(f"**#{i}** `{d.metadata}`")
                st.text(d.page_content)

        with st.expander("디버그: 재순위 코사인 점수"):
            st.json(
                {
                    "rerank_scores": rr.details.get("rerank_scores"),
                    "hybrid_top_mean": rr.details.get("hybrid_top_mean"),
                }
            )


if __name__ == "__main__":
    main()
