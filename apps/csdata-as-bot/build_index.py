"""JSONL 레코드를 OpenAI 임베딩 + Chroma 로컬 DB에 적재합니다.

진행 상황을 보기 위해 배치 단위로 upsert 하며 로그를 출력합니다.
BM25용 sparse 인덱스(`sparse_index.pkl`)를 동일 폴더에 함께 저장합니다.
"""
from __future__ import annotations

import json
import os
import pickle
import re
from datetime import datetime
from pathlib import Path

from langchain_chroma import Chroma
from langchain_core.documents import Document
from langchain_openai import OpenAIEmbeddings
from rank_bm25 import BM25Okapi

from normalizer import error_code_norm_field, normalize_symptom_text, tokenize_for_bm25

HERE = Path(__file__).resolve().parent
try:
    from dotenv import load_dotenv

    load_dotenv(HERE.parents[1] / ".env")
except ImportError:
    pass

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


def enrich_metadata(docs: list[Document]) -> list[Document]:
    """구 JSONL 호환: 정규화 필드·doc_id용 인덱스 메타 보강."""
    out: list[Document] = []
    for i, d in enumerate(docs):
        md = dict(d.metadata or {})
        if not md.get("symptom_norm"):
            # page_content에서 증상 줄만 대략 추출
            m = re.search(r"증상/접수:\s*(.+?)(?:\n조치|$)", d.page_content, re.S)
            raw_sym = m.group(1).strip() if m else ""
            md["symptom_norm"] = normalize_symptom_text(raw_sym)
        if not md.get("error_code_norm"):
            md["error_code_norm"] = error_code_norm_field(d.page_content)
        md["chunk_index"] = i
        md["doc_id"] = f"as-{i}"
        out.append(Document(page_content=d.page_content, metadata=md))
    return out


def save_sparse_index(run_dir: Path, docs: list[Document]) -> None:
    tokenized = [tokenize_for_bm25(d.page_content) for d in docs]
    # BM25Okapi는 pickle 직렬화가 환경에 따라 불안정해 토큰만 저장 후 로드 시 재구성
    payload = {
        "tokenized_corpus": tokenized,
        "n_docs": len(docs),
    }
    out = run_dir / "sparse_index.pkl"
    with out.open("wb") as f:
        pickle.dump(payload, f, protocol=pickle.HIGHEST_PROTOCOL)
    # 로드 시 검증용으로 BM25 한 번 생성
    _ = BM25Okapi(tokenized)
    print(f"  - sparse(BM25) 인덱스 저장: {out}")


def main() -> None:
    if not os.environ.get("OPENAI_API_KEY"):
        raise SystemExit("OPENAI_API_KEY 환경변수를 설정하세요.")
    docs = enrich_metadata(load_docs())
    total = len(docs)
    if total == 0:
        raise SystemExit(
            f"문서가 없습니다: {JSONL}\n"
            "먼저 프로젝트 루트에 csData 엑셀이 있는지 확인한 뒤:\n"
            "  poetry run python scripts/csdata_as_bot/ingest.py"
        )

    # Windows 파일 잠금 회피: 매 실행마다 새 폴더에 인덱스를 생성
    run_dir = CHROMA_DIR.with_name(f"chroma_db_{datetime.now().strftime('%Y%m%d_%H%M%S')}")
    print(f"[1/5] 인덱스 경로: {run_dir}")
    print(f"[2/5] 임베딩 모델 준비 (문서 {total}건)")
    emb = OpenAIEmbeddings(model="text-embedding-3-small")
    run_dir.mkdir(parents=True, exist_ok=True)
    vs = Chroma(
        persist_directory=str(run_dir),
        embedding_function=emb,
        collection_name="csdata_as",
    )

    batch_size = 100
    print(f"[3/5] 배치 적재 시작 (batch_size={batch_size})")
    for start in range(0, total, batch_size):
        end = min(start + batch_size, total)
        batch = docs[start:end]
        ids = [f"as-{i}" for i in range(start, end)]
        vs.add_documents(batch, ids=ids)
        pct = (end / total) * 100
        print(f"  - {end}/{total} ({pct:.1f}%)")

    print("[4/5] BM25 sparse 인덱스 생성")
    save_sparse_index(run_dir, docs)

    active_marker = HERE / "active_chroma_dir.txt"
    active_marker.write_text(run_dir.resolve().as_posix(), encoding="utf-8")
    print(f"[5/5] 완료: {total}건 인덱싱 -> {run_dir}")
    print(f"  - Streamlit 기본 경로 힌트 저장: {active_marker}")


if __name__ == "__main__":
    main()
