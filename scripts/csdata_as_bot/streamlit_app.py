"""
증상/에러 설명을 입력하면 csData 기반 유사 AS 사례와 조치 요약을 보여줍니다.

실행:
  cd 프로젝트 루트
  poetry run streamlit run scripts/csdata_as_bot/streamlit_app.py

사전:
  poetry run python scripts/csdata_as_bot/ingest.py
  poetry run python scripts/csdata_as_bot/build_index.py
"""
from __future__ import annotations

import os
from pathlib import Path

import streamlit as st
from langchain_chroma import Chroma
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI, OpenAIEmbeddings

HERE = Path(__file__).resolve().parent
CHROMA_DIR = HERE / "chroma_db"

SYS = """당신은 전기차 충전기 AS(애프터서비스) 지원 도우미입니다.
반드시 제공된 [참고 사례] 안의 내용만 근거로 답합니다.
참고 사례에 없는 추측·일반론은 하지 마세요.
답변 구조:
1) 유사 증상으로 보이는 과거 사례 요약 (출처 파일/시트 표기)
2) 실제 현장에서 했던 조치·교체 부품 (사례에 있는 그대로)
3) 추가 확인이 필요하면 무엇을 보면 좋은지 (사례 범위 내에서만)

면책: 최종 판단·안전·전기 작업은 반드시 담당 엔지니어가 수행해야 합니다."""


def get_vectorstore():
    if not CHROMA_DIR.exists():
        return None
    emb = OpenAIEmbeddings(model="text-embedding-3-small")
    return Chroma(
        persist_directory=str(CHROMA_DIR),
        embedding_function=emb,
        collection_name="csdata_as",
    )


def main() -> None:
    st.set_page_config(page_title="충전기 AS 증상·조치 봇", layout="wide")
    st.title("전기차 충전기 AS — 증상·조치 참조 봇")
    st.caption("csData 엑셀을 인덱싱한 검색형 보조 도구입니다. 법적/안전 책임은 담당자에게 있습니다.")

    if not os.environ.get("OPENAI_API_KEY"):
        st.error("OPENAI_API_KEY 가 설정되어 있지 않습니다. `.env` 또는 환경변수로 추가하세요.")
        return

    vs = get_vectorstore()
    if vs is None:
        st.warning(
            f"Chroma 인덱스가 없습니다. 터미널에서 순서대로 실행하세요:\n"
            f"`python scripts/csdata_as_bot/ingest.py`\n"
            f"`python scripts/csdata_as_bot/build_index.py`"
        )
        return

    q = st.text_area(
        "증상·에러·현상을 입력하세요 (예: 에러코드 23, RFID 인식 안 됨, PLC 하트비트 없음)",
        height=120,
    )
    k = st.slider("참고 사례 개수", 3, 15, 6)

    if st.button("유사 사례 검색 및 답변", type="primary") and q.strip():
        retriever = vs.as_retriever(search_kwargs={"k": k})
        docs = retriever.invoke(q.strip())
        ctx = "\n\n---\n\n".join(d.page_content for d in docs)

        llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)
        prompt = ChatPromptTemplate.from_messages(
            [
                ("system", SYS),
                (
                    "human",
                    "[참고 사례]\n{context}\n\n---\n사용자 질문:\n{question}",
                ),
            ]
        )
        chain = prompt | llm
        with st.spinner("생성 중…"):
            msg = chain.invoke({"context": ctx, "question": q.strip()})

        st.subheader("답변")
        st.write(msg.content)

        with st.expander("검색에 사용된 원문 청크"):
            for i, d in enumerate(docs, 1):
                st.markdown(f"**#{i}** `{d.metadata}`")
                st.text(d.page_content)


if __name__ == "__main__":
    main()
