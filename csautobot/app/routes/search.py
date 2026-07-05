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
from services.ai_provider import AiProviderConfigPayload, invoke_structured_output
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

class SearchResponse(BaseModel):
    structured: AnswerSchema
    confidence: float
    level: str
    candidate_count: int
    openai_error: bool
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

면책: 최종 판단·안전·전기 작업은 반드시 담당 엔지니어가 수행해야 합니다."""

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
    ai_config = resolve_ai_config_for_request(db, tenant_id, req.ai_config)

    index_dir = resolve_chroma_dir(HERE)
    if not index_dir:
        raise HTTPException(status_code=500, detail="Chroma DB index directory not found. Please run build_index.py first.")

    bm25 = load_bm25(index_dir)
    emb = OpenAIEmbeddings(model="text-embedding-3-small")
    vs = _get_vs(index_dir)

    web_results = []
    if req.use_web_search:
        web_results = _run_tavily_search(req.query.strip())

    # RAG Retrieval
    rr = retrieve_reranked(
        req.query.strip(), vs, bm25, emb,
        k_dense=req.k_dense, k_sparse=req.k_sparse, k_hybrid=req.k_hybrid, k_final=5
    )
    
    openai_error_occured = rr.details.get("openai_error", False)
    docs = rr.documents
    ctx = "\n\n---\n\n".join(d.page_content for d in docs)

    web_ctx = ""
    if web_results:
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

    invoke_inputs = {
        "context": ctx,
        "web_context": web_ctx,
        "question": req.query.strip(),
    }

    structured = None
    try:
        structured, _model_label = invoke_structured_output(
            AnswerSchema,
            system_prompt=SYS,
            human_template=guard + "[로컬 참고 사례]\n{context}\n\n{web_context}---\n사용자 질문:\n{question}",
            inputs=invoke_inputs,
            ai_config=ai_config,
        )
    except Exception as e2:
        import logging
        logging.warning(f"All LLMs failed for as-cases search: {e2}")
        structured = AnswerSchema(
            symptom_summary="AI 분석 서비스를 일시적으로 사용할 수 없습니다. 잠시 후 다시 시도해주세요.",
            top_causes=[],
            inspection_steps=["서비스 복구 후 재시도 권장"],
            parts="사례에 명시 없음",
            evidence_refs=[],
            confidence_note="AI 서비스 일시 중단 중 (API 할당량 초과 또는 모델 오류)"
        )

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

    record_usage(tenant_id, FEATURE_RAG_SEARCH)

    return SearchResponse(
        structured=structured,
        confidence=rr.confidence,
        level=rr.level,
        candidate_count=rr.details.get("candidate_count", 0),
        openai_error=openai_error_occured or not llm_success,
        web_results=web_results,
        metadata_docs=metadata_docs
    )
