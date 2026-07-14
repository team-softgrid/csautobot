import os
import sys
from pathlib import Path
from typing import Any, List, Optional, Union
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from langchain_chroma import Chroma
from langchain_openai import OpenAIEmbeddings
from sqlalchemy.orm import Session
from retrieval import load_bm25, resolve_chroma_dir, retrieve_reranked
from services.ai_provider import AiProviderConfigPayload, AiUsageInfo, invoke_structured_output, usage_for_non_llm
from services.tenant_ai_settings import resolve_ai_config_for_request
from storage.db import get_db

# Setup python path
HERE = Path(__file__).resolve().parent.parent.parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))

router = APIRouter(tags=["Search"])

# Pydantic Schemas
class SearchRequest(BaseModel):
    query: str = Field(..., min_length=1, max_length=2000)
    tenant_id: str = "default_tenant"
    use_web_search: bool = False
    k_hybrid: int = 30
    k_dense: int = 50
    k_sparse: int = 50
    ai_config: AiProviderConfigPayload | None = None

class AnswerSchema(BaseModel):
    symptom_summary: str = Field(description="유사 사례 기준 증상 요약")
    top_causes: List[str] = Field(default_factory=list, max_length=3)
    inspection_steps: List[str] = Field(default_factory=list)
    parts: str = Field(description="필요 부품 또는 사례 부재 시 안내")
    evidence_refs: List[str] = Field(default_factory=list)
    confidence_note: str = Field(description="신뢰도·주의사항")

# Groq llama-3.1-8b-instant on-demand TPM ≈ 6000. Long RAG+web prompts
# previously hit 413 (Requested 6866). Keep LLM context comfortably under that.
_MAX_DOC_CHARS = 1200
_MAX_CONTEXT_CHARS = 4500
_MAX_WEB_CHARS = 1200


def _clip_text(text: str, limit: int) -> str:
    raw = (text or "").strip()
    if len(raw) <= limit:
        return raw
    return raw[: max(0, limit - 1)].rstrip() + "…"


def _build_llm_context(docs: list) -> str:
    chunks: list[str] = []
    used = 0
    for d in docs:
        piece = _clip_text(getattr(d, "page_content", "") or "", _MAX_DOC_CHARS)
        if not piece:
            continue
        sep = 4 if chunks else 0  # len("\n\n---\n\n") approx handled below
        block = piece if not chunks else f"\n\n---\n\n{piece}"
        if used + len(block) > _MAX_CONTEXT_CHARS:
            remain = _MAX_CONTEXT_CHARS - used - (sep + 1)
            if remain < 80:
                break
            truncated = _clip_text(piece, remain)
            chunks.append(truncated)
            break
        chunks.append(piece)
        used += len(block)
    return "\n\n---\n\n".join(chunks)

class SearchResponse(BaseModel):
    structured: AnswerSchema
    confidence: float
    level: str
    candidate_count: int
    openai_error: bool  # legacy: embedding(OpenAI) degraded to BM25-only
    embedding_degraded: bool = False
    llm_error: bool = False
    llm_model: str | None = None
    ai_usage: AiUsageInfo | None = None
    web_results: List[Any] = []
    metadata_docs: List[Any] = []

SYS = """당신은 전기차 충전기 AS(애프터서비스) 지원 도우미입니다.
반드시 제공된 [참고 사례] 안의 내용만 근거로 답합니다.
참고 사례에 없는 추측·일반론은 하지 마세요.

출력은 지정된 JSON 스키마를 따릅니다. 각 필드는 한국어로 작성합니다.
- evidence_refs: 참고 사례 출처를 `파일경로 | 시트` 형태로 짧게 나열 (최대 5개)
- top_causes: 참고 사례에 근거가 있는 경우만 최대 3개. 근거가 없으면 빈 배열
- inspection_steps: 사례에 나온 점검/조치 순서를 요약한 단계 리스트
- parts: 사례에 언급된 교체 부품이 있으면 그대로, 없으면 "사례에 명시 없음"
- confidence_note: 시스템이 제공한 신뢰도 등급(high/mid/low)에 맞는 주의 문구

면책: 최종 판단·안전·전기 작업은 반드시 담당 엔지니어가 수행해야 합니다.

JSON 출력 시 반드시 아래 영문 키만 사용하세요:
symptom_summary, top_causes, inspection_steps, parts, evidence_refs, confidence_note"""


def _openai_embedding_available() -> bool:
    key = os.environ.get("OPENAI_API_KEY", "").strip()
    return bool(key) and key.startswith("sk-") and len(key) > 20


def _answer_from_faq(query: str, faq_text: str) -> AnswerSchema:
    steps = [ln for ln in faq_text.split("\n") if ln.strip()]
    return AnswerSchema(
        symptom_summary=f"FAQ: {query}",
        top_causes=[steps[0]] if steps else [],
        inspection_steps=steps or [faq_text],
        parts="사례에 명시 없음",
        evidence_refs=["FAQ 단축 경로"],
        confidence_note="FAQ exact-match — LLM 미사용",
    )


def _answer_from_docs(query: str, docs: list, level: str) -> AnswerSchema:
    refs: list[str] = []
    steps: list[str] = []
    for d in docs[:3]:
        meta = d.metadata or {}
        src = meta.get("source_file") or meta.get("source") or "로컬 DB"
        sheet = meta.get("sheet") or ""
        refs.append(f"{src} | {sheet}".strip(" |"))
        snippet = (d.page_content or "").split("\n")[0][:120]
        if snippet:
            steps.append(snippet)
    return AnswerSchema(
        symptom_summary=f"'{query}' — 유사 AS 사례 {len(docs)}건 검색 (LLM 미사용 fallback)",
        top_causes=[query],
        inspection_steps=steps or ["하단 '검색·재순위 청크' 원문을 확인하세요."],
        parts="사례에 명시 없음",
        evidence_refs=refs[:5],
        confidence_note=f"BM25/RAG 검색 결과 기반 (신뢰도 {level})",
    )

def _get_vs(chroma_dir: Path) -> Chroma:
    emb = OpenAIEmbeddings(model="text-embedding-3-small")
    return Chroma(
        persist_directory=str(chroma_dir),
        embedding_function=emb,
        collection_name="csautobot",
    )

def _run_tavily_search(query: str) -> List[Any]:
    try:
        from langchain_community.tools.tavily_search import TavilySearchResults
        if not os.environ.get("TAVILY_API_KEY"):
            return []
        technical_query = f"전기차 충전기 {query} 고장 점검 조치 수리"
        search = TavilySearchResults(max_results=5)
        res = search.invoke({"query": technical_query})
        if isinstance(res, str):
            return []
        return res
    except Exception:
        return []

@router.post("/search/as-cases", response_model=SearchResponse)
def search_as_cases(req: SearchRequest, db: Session = Depends(get_db)):
    from services.billing_metering import (
        FEATURE_RAG_SEARCH,
        check_quota,
        record_usage,
    )

    tenant_id = (req.tenant_id or "default_tenant").strip()
    check_quota(tenant_id, FEATURE_RAG_SEARCH)
    try:
        ai_config = resolve_ai_config_for_request(db, tenant_id, req.ai_config)
    except Exception as cfg_exc:
        print(f"AI config load failed, using env defaults: {cfg_exc}")
        ai_config = None

    from services.faq_shortcut import try_shortcut

    faq = try_shortcut(req.query.strip())
    if faq:
        structured = _answer_from_faq(req.query.strip(), faq)
        faq_usage = usage_for_non_llm("faq-shortcut")
        try:
            record_usage(
                tenant_id,
                FEATURE_RAG_SEARCH,
                model_name=faq_usage.model_label,
                shortcut=True,
            )
        except Exception as usage_exc:
            print(f"Usage metering failed (search still returned): {usage_exc}")
        return SearchResponse(
            structured=structured,
            confidence=0.85,
            level="mid",
            candidate_count=0,
            openai_error=False,
            embedding_degraded=False,
            llm_error=False,
            llm_model="faq-shortcut",
            ai_usage=faq_usage,
            web_results=[],
            metadata_docs=[],
        )

    index_dir = resolve_chroma_dir(HERE)
    if not index_dir:
        raise HTTPException(status_code=500, detail="Chroma DB index directory not found. Please run build_index.py first.")

    bm25 = load_bm25(index_dir)
    vs = _get_vs(index_dir)
    emb = OpenAIEmbeddings(model="text-embedding-3-small") if _openai_embedding_available() else None

    web_results = []
    if req.use_web_search:
        web_results = _run_tavily_search(req.query.strip())

    if emb is None:
        print("Search RAG: OpenAI embedding unavailable, using BM25-only retrieval")
        from retrieval import hybrid_candidate_indices, get_documents_by_indices, estimate_confidence

        top_idx, hybrid, openai_error_occured = hybrid_candidate_indices(
            req.query.strip(), vs, bm25,
            k_dense=0, k_sparse=req.k_sparse, k_merge=req.k_hybrid,
        )
        docs = get_documents_by_indices(vs, top_idx[:5])
        hybrid_scores = [hybrid.get(i, 0.0) for i in top_idx[:5]]
        rr_confidence, rr_level = estimate_confidence(
            hybrid_scores, req.query.strip(), docs[0] if docs else None,
        )
        rr_details = {
            "openai_error": True,
            "candidate_count": len(top_idx),
            "rerank": "skipped-no-embedding",
        }
    else:
        rr = retrieve_reranked(
            req.query.strip(), vs, bm25, emb,
            k_dense=req.k_dense, k_sparse=req.k_sparse, k_hybrid=req.k_hybrid, k_final=5,
        )
        openai_error_occured = rr.details.get("openai_error", False)
        docs = rr.documents
        rr_details = rr.details
        rr_level = rr.level
        rr_confidence = rr.confidence
    ctx = _build_llm_context(docs)

    web_ctx = ""
    if web_results:
        lines = []
        for res in web_results:
            if isinstance(res, dict):
                title = res.get('title', '')
                content = _clip_text(str(res.get('content', '') or ""), 280)
                lines.append(f"- [{title}] {content}")
        if lines:
            web_ctx = _clip_text(
                "[웹 리서치 참고 자료]\n" + "\n".join(lines) + "\n\n",
                _MAX_WEB_CHARS,
            )

    guard = ""
    if rr_level == "low":
        guard = (
            "[운영 지침] 신뢰도 등급: low. 근거가 약할 수 있음을 사용자에게 명확히 알리고, "
            "현장 점검·추가 데이터 확인을 권고하세요. 참고 사례 및 웹 리서치 밖의 추측은 금지입니다.\n\n"
        )
    elif rr_level == "mid":
        guard = (
            "[운영 지침] 신뢰도 등급: mid. 답변은 보조용이며 필수 확인 사항을 빠짐없이 적으세요.\n\n"
        )

    invoke_inputs = {
        "context": ctx,
        "web_context": web_ctx,
        "question": req.query.strip(),
    }

    structured = None
    llm_success = False
    model_label: str | None = None
    ai_usage: AiUsageInfo | None = None
    try:
        structured, ai_usage = invoke_structured_output(
            AnswerSchema,
            system_prompt=SYS,
            human_template=guard + "[로컬 참고 사례]\n{context}\n\n{web_context}---\n사용자 질문:\n{question}",
            inputs=invoke_inputs,
            ai_config=ai_config,
            task_type="general",
        )
        llm_success = True
        model_label = ai_usage.model_label
    except Exception as e2:
        import logging
        logging.warning(f"All LLMs failed for as-cases search: {e2}")
        structured = _answer_from_docs(req.query.strip(), docs, rr_level)
        llm_success = False
        model_label = "offline-rules"
        ai_usage = usage_for_non_llm("offline-rules")

    if structured is None:
        structured = AnswerSchema(
            symptom_summary="AI 분석 서비스를 일시적으로 사용할 수 없습니다.",
            top_causes=[],
            inspection_steps=[],
            parts="사례에 명시 없음",
            evidence_refs=[],
            confidence_note="AI 서비스 일시 중단",
        )

    # Build response format metadata docs
    metadata_docs = []
    for d in docs:
        metadata_docs.append({
            "page_content": d.page_content,
            "metadata": d.metadata
        })

    embedding_degraded = bool(openai_error_occured)

    try:
        record_usage(
            tenant_id,
            FEATURE_RAG_SEARCH,
            model_name=model_label,
            input_tokens=(ai_usage.input_tokens if ai_usage else 0),
            output_tokens=(ai_usage.output_tokens if ai_usage else 0),
            fallback_provider=(ai_usage.fallback_provider if ai_usage else None),
        )
    except Exception as usage_exc:
        print(f"Usage metering failed (search still returned): {usage_exc}")

    return SearchResponse(
        structured=structured,
        confidence=rr_confidence,
        level=rr_level,
        candidate_count=rr_details.get("candidate_count", 0),
        openai_error=embedding_degraded,
        embedding_degraded=embedding_degraded,
        llm_error=not llm_success,
        llm_model=model_label,
        ai_usage=ai_usage,
        web_results=web_results,
        metadata_docs=metadata_docs,
    )
