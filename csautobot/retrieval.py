"""
하이브리드(Dense+BM25) 검색, 임베딩 기반 재순위, 신뢰도 추정.

설계: docs/rag-improvement-design.md §3.2~3.4
"""
from __future__ import annotations

import pickle
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np
from langchain_chroma import Chroma
from langchain_core.documents import Document

from normalizer import extract_error_code_keys, tokenize_for_bm25


@dataclass
class RetrievalResult:
    documents: list[Document]
    confidence: float
    level: str
    details: dict[str, Any]


def _index_dir_ready(p: Path) -> bool:
    """하이브리드 파이프라인: Chroma 폴더 + BM25 pickle 이 같이 있어야 함."""
    return p.is_dir() and (p / "sparse_index.pkl").is_file()


def resolve_chroma_dir(here: Path) -> Path | None:
    """active_chroma_dir.txt 또는 수정 시각 기준으로, sparse 포함 완전한 인덱스만 반환."""
    marker = here / "active_chroma_dir.txt"
    if marker.exists():
        raw = marker.read_text(encoding="utf-8").strip()
        if raw:
            p = Path(raw)
            if _index_dir_ready(p):
                return p
    candidates = sorted(
        [x for x in here.glob("chroma_db*") if x.is_dir()],
        key=lambda x: x.stat().st_mtime,
        reverse=True,
    )
    for p in candidates:
        if _index_dir_ready(p):
            return p
    return None


def load_bm25(chroma_dir: Path) -> Any:
    from rank_bm25 import BM25Okapi

    path = chroma_dir / "sparse_index.pkl"
    if not path.is_file():
        raise FileNotFoundError(f"BM25 인덱스 없음: {path} (build_index.py 재실행)")
    with path.open("rb") as f:
        data = pickle.load(f)
    return BM25Okapi(data["tokenized_corpus"])


def _min_max_norm(scores: dict[int, float]) -> dict[int, float]:
    if not scores:
        return {}
    vals = list(scores.values())
    lo, hi = min(vals), max(vals)
    if hi - lo < 1e-12:
        return {k: 1.0 for k in scores}
    return {k: (v - lo) / (hi - lo) for k, v in scores.items()}


def _code_bonus(query: str, doc_meta: dict[str, Any], alpha: float = 0.15) -> float:
    q_codes = set(extract_error_code_keys(query))
    if not q_codes:
        return 0.0
    raw = (doc_meta or {}).get("error_code_norm") or ""
    d_codes = {x for x in raw.split("|") if x}
    return alpha if q_codes & d_codes else 0.0


def hybrid_candidate_indices(
    query: str,
    vs: Chroma,
    bm25: Any,
    k_dense: int = 50,
    k_sparse: int = 50,
    k_merge: int = 30,
) -> tuple[list[int], dict[int, float]]:
    """Dense+Sparse 결합 점수 상위 chunk_index 반환."""
    q_tok = tokenize_for_bm25(query)
    sparse_scores = np.asarray(bm25.get_scores(q_tok), dtype=np.float64)
    n = sparse_scores.shape[0]
    if n == 0:
        return [], {}

    sparse_order = np.argsort(-sparse_scores)[:k_sparse]
    dense_hits = vs.similarity_search_with_score(query, k=k_dense)

    dense_raw: dict[int, float] = {}
    for doc, dist in dense_hits:
        idx = doc.metadata.get("chunk_index")
        if idx is None:
            continue
        idx = int(idx)
        # 거리 → 유사도 (낮은 거리가 더 좋음)
        sim = 1.0 / (1.0 + float(dist))
        dense_raw[idx] = max(dense_raw.get(idx, 0.0), sim)

    sparse_raw = {int(i): float(sparse_scores[i]) for i in sparse_order}

    union_keys = set(dense_raw) | set(sparse_raw)
    if dense_raw:
        nd = _min_max_norm({k: dense_raw[k] for k in union_keys if k in dense_raw})
        for k in union_keys:
            if k not in nd:
                nd[k] = 0.0
    else:
        nd = {k: 0.0 for k in union_keys}

    ns = _min_max_norm(sparse_raw) if sparse_raw else {k: 0.0 for k in union_keys}
    for k in union_keys:
        if k not in ns:
            ns[k] = 0.0

    hybrid: dict[int, float] = {}
    for k in union_keys:
        d = nd.get(k, 0.0)
        s = ns.get(k, 0.0)
        hybrid[k] = 0.65 * d + 0.35 * s

    # 코드 일치 보너스: 상위 후보만 메타 조회
    ranked_pre = sorted(hybrid.keys(), key=lambda x: hybrid[x], reverse=True)[: max(k_merge, 80)]
    metas = vs.get(
        ids=[f"as-{i}" for i in ranked_pre],
        include=["metadatas"],
    )
    meta_list = metas.get("metadatas") or []
    id_list = metas.get("ids") or []
    id_to_meta = dict(zip(id_list, meta_list))

    for k in ranked_pre:
        meta = id_to_meta.get(f"as-{k}") or {}
        hybrid[k] = hybrid.get(k, 0.0) + _code_bonus(query, meta)

    top_idx = sorted(hybrid.keys(), key=lambda x: hybrid[x], reverse=True)[:k_merge]
    return top_idx, hybrid


def get_documents_by_indices(vs: Chroma, indices: list[int]) -> list[Document]:
    if not indices:
        return []
    ids = [f"as-{i}" for i in indices]
    got = vs.get(ids=ids, include=["documents", "metadatas"])
    docs_map: dict[str, Document] = {}
    for did, text, meta in zip(
        got.get("ids") or [],
        got.get("documents") or [],
        got.get("metadatas") or [],
    ):
        docs_map[str(did)] = Document(page_content=text or "", metadata=dict(meta or {}))
    return [docs_map[f"as-{i}"] for i in indices if f"as-{i}" in docs_map]


def rerank_by_embedding(
    emb: Any,
    query: str,
    docs: list[Document],
    top_k: int = 5,
    max_chars: int = 3500,
) -> tuple[list[Document], list[float]]:
    """동일 임베딩 공간에서 코사인 유사도로 재순위 (FlashRank 미설치 환경 대비)."""
    if not docs:
        return [], []
    texts = [d.page_content[:max_chars] for d in docs]
    qv = np.asarray(emb.embed_query(query), dtype=np.float64)
    dvs = np.asarray(emb.embed_documents(texts), dtype=np.float64)
    qn = qv / (np.linalg.norm(qv) + 1e-9)
    dn = dvs / (np.linalg.norm(dvs, axis=1, keepdims=True) + 1e-9)
    sims = dn @ qn
    order = np.argsort(-sims)
    top = order[:top_k]
    reranked = [docs[int(i)] for i in top]
    scores = [float(sims[int(i)]) for i in top]
    return reranked, scores


def estimate_confidence(
    rerank_scores: list[float],
    query: str,
    top_doc: Document | None,
) -> tuple[float, str]:
    """
    임계값 예시(문서): >=0.75 high, 0.45~ mid, < low
    """
    if not rerank_scores:
        return 0.0, "low"
    mean_s = float(np.mean(rerank_scores))
    margin = float(rerank_scores[0] - rerank_scores[1]) if len(rerank_scores) > 1 else float(rerank_scores[0])
    std_s = float(np.std(rerank_scores)) if len(rerank_scores) > 1 else 0.0

    q_codes = set(extract_error_code_keys(query))
    top_codes = set((top_doc.metadata.get("error_code_norm") or "").split("|")) if top_doc else set()
    top_codes.discard("")
    code_hit = 1.0 if q_codes and (q_codes & top_codes) else 0.0

    # 0~1 스케일로 압축
    conf = (
        0.42 * mean_s
        + 0.28 * min(1.0, max(0.0, margin * 6.0))
        + 0.22 * code_hit
        + 0.08 * max(0.0, 1.0 - min(1.0, std_s * 4.0))
    )
    conf = float(max(0.0, min(1.0, conf)))
    if conf >= 0.75:
        level = "high"
    elif conf >= 0.45:
        level = "mid"
    else:
        level = "low"
    return conf, level


def retrieve_reranked(
    query: str,
    vs: Chroma,
    bm25: Any,
    emb: Any,
    k_dense: int = 50,
    k_sparse: int = 50,
    k_hybrid: int = 30,
    k_final: int = 5,
) -> RetrievalResult:
    cand_idx, hybrid_scores = hybrid_candidate_indices(
        query, vs, bm25, k_dense=k_dense, k_sparse=k_sparse, k_merge=k_hybrid
    )
    cand_docs = get_documents_by_indices(vs, cand_idx)

    reranked, scores = rerank_by_embedding(emb, query, cand_docs, top_k=k_final)
    conf, level = estimate_confidence(scores, query, reranked[0] if reranked else None)
    return RetrievalResult(
        documents=reranked,
        confidence=conf,
        level=level,
        details={
            "rerank_scores": scores,
            "hybrid_top_mean": float(np.mean([hybrid_scores[i] for i in cand_idx[:k_final]]))
            if cand_idx
            else 0.0,
            "candidate_count": len(cand_docs),
        },
    )
