"""JSONL 레코드를 OpenAI 임베딩 + Chroma 로컬 DB에 적재합니다.

진행 상황을 보기 위해 배치 단위로 upsert 하며 로그를 출력합니다.
"""
from __future__ import annotations

import json
import os
from datetime import datetime
from pathlib import Path

from langchain_chroma import Chroma
from langchain_core.documents import Document
from langchain_openai import OpenAIEmbeddings

HERE = Path(__file__).resolve().parent
JSONL = HERE / "as_records.jsonl"
CHROMA_DIR = HERE / "chroma_db"


def load_docs() -> list[Document]:
    docs: list[Document] = []
    if not JSONL.exists():
        raise SystemExit(f"먼저 실행: python ingest.py  (없음: {JSONL})")
    with JSONL.open(encoding="utf-8") as f:
        for line in f:
            o = json.loads(line)
            docs.append(Document(page_content=o["page_content"], metadata=o.get("metadata") or {}))
    return docs


def main() -> None:
    if not os.environ.get("OPENAI_API_KEY"):
        raise SystemExit("OPENAI_API_KEY 환경변수를 설정하세요.")
    docs = load_docs()
    total = len(docs)
    if total == 0:
        raise SystemExit(f"문서가 없습니다: {JSONL}")

    # Windows 파일 잠금 회피: 매 실행마다 새 폴더에 인덱스를 생성
    run_dir = CHROMA_DIR.with_name(f"chroma_db_{datetime.now().strftime('%Y%m%d_%H%M%S')}")
    print(f"[1/4] 인덱스 경로: {run_dir}")
    print(f"[2/4] 임베딩 모델 준비 (문서 {total}건)")
    emb = OpenAIEmbeddings(model="text-embedding-3-small")
    run_dir.mkdir(parents=True, exist_ok=True)
    vs = Chroma(
        persist_directory=str(run_dir),
        embedding_function=emb,
        collection_name="csdata_as",
    )

    batch_size = 100
    print(f"[3/4] 배치 적재 시작 (batch_size={batch_size})")
    for start in range(0, total, batch_size):
        end = min(start + batch_size, total)
        batch = docs[start:end]
        ids = [f"as-{i}" for i in range(start, end)]
        vs.add_documents(batch, ids=ids)
        pct = (end / total) * 100
        print(f"  - {end}/{total} ({pct:.1f}%)")

    print(f"[4/4] 완료: {total}건 인덱싱 -> {run_dir}")


if __name__ == "__main__":
    main()
