import os
import sys
from pathlib import Path
from typing import Any, List, Optional
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

# Setup python path
HERE = Path(__file__).resolve().parent.parent.parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))

from storage.db import get_db
from storage import repositories as repo
from services import inspection_service as svc
from services.ai_provider import AiProviderConfigPayload, AiUsageInfo
from services.tenant_ai_settings import resolve_ai_config_for_request

router = APIRouter(tags=["Inspection"])

# Schemas
class ChecklistItem(BaseModel):
    item: str
    status: str
    note: str = ""

class PresetResponse(BaseModel):
    checklist: List[ChecklistItem]

class DraftRequest(BaseModel):
    target: str
    cycle: str
    checklist: List[ChecklistItem]
    memo: str = ""
    tenant_id: str = "default_tenant"
    site_name: Optional[str] = None
    inspection_type: str = "정기점검"
    ai_config: Optional[AiProviderConfigPayload] = None

class AiExecutionMeta(BaseModel):
    endpoint: str = "POST /api/v1/inspection/draft"
    generation_path: str = Field(description="faq-shortcut | llm | offline-rules")
    model_label: str = Field(description="실제 사용 경로/모델 라벨")
    provider: str | None = None
    model_name: str | None = None
    task_type: str | None = None
    provider_chain: List[str] = Field(default_factory=list)
    description: str = ""
    input_tokens: int = 0
    output_tokens: int = 0
    total_tokens: int = 0
    latency_ms: int = 0


class DraftResponse(BaseModel):
    draft_text: str
    summary_json: Any
    ai_meta: AiExecutionMeta

def _retrieve_similar_cases(query: str) -> List[dict[str, Any]]:
    if not query:
        return []
    try:
        from langchain_chroma import Chroma
        from retrieval import load_bm25, resolve_chroma_dir, retrieve_reranked
        from app.embeddings import get_embedding_function
        
        index_dir = resolve_chroma_dir(HERE)
        if not index_dir:
            return []
            
        vs = Chroma(
            persist_directory=str(index_dir),
            embedding_function=get_embedding_function(),
            collection_name="csautobot",
        )
        bm25 = load_bm25(index_dir)
        if not bm25:
            return []
            
        emb = get_embedding_function()
        rr = retrieve_reranked(
            query, vs, bm25, emb,
            k_dense=20, k_sparse=20, k_hybrid=10, k_final=3,
        )
        
        res = []
        for d in rr.documents:
            res.append({
                "symptom": d.metadata.get("symptom_norm", ""),
                "action": d.page_content,
                "title": f"과거 유사 사례 (출처: {d.metadata.get('source', '알수없음')})"
            })
        return res
    except Exception as e:
        print(f"Inspection RAG search failed: {e}")
        return []

def _resolve_inspection_task_type(checklist: List[ChecklistItem], cycle: str) -> str:
    has_issue = any(x.status in ("이상", "주의") for x in checklist)
    if has_issue or cycle in {"분기", "반기", "연간"}:
        return "inspection_detail"
    return "inspection_basic"


def _build_ai_execution_meta(
    used_model: str,
    ai_config: AiProviderConfigPayload | None,
    *,
    task_type: str,
    usage: AiUsageInfo | None = None,
) -> AiExecutionMeta:
    from services.ai_provider import _provider_chain, route_by_task

    if used_model == "faq-shortcut":
        path = "faq-shortcut"
        desc = "FAQ exact-match 단축 경로 — LLM API 호출 없음"
        chain: list[str] = []
    elif used_model == "offline-rules":
        path = "offline-rules"
        desc = "LLM 전체 실패 후 규칙 기반 오프라인 초안"
        if usage and usage.fallback_reason:
            desc += f" — 시도 내역: {usage.fallback_reason}"
        chain = _provider_chain(route_by_task(task_type, ai_config))  # type: ignore[arg-type]
    else:
        path = "llm"
        desc = f"Hybrid LLM structured output (task: {task_type})"
        chain = _provider_chain(route_by_task(task_type, ai_config))  # type: ignore[arg-type]

    provider: str | None = None
    model_name: str | None = None
    label = used_model.split("->", 1)[-1] if "->" in used_model else used_model
    if ":" in label:
        provider, model_name = label.split(":", 1)

    input_tokens = usage.input_tokens if usage else 0
    output_tokens = usage.output_tokens if usage else 0
    return AiExecutionMeta(
        generation_path=path,
        model_label=used_model,
        provider=provider,
        model_name=model_name,
        task_type=task_type,
        provider_chain=chain,
        description=desc,
        input_tokens=input_tokens,
        output_tokens=output_tokens,
        total_tokens=input_tokens + output_tokens,
        latency_ms=usage.latency_ms if usage else 0,
    )

class LogCreateRequest(BaseModel):
    inspection_id: str
    tenant_id: str = "default_tenant"
    site_id: str
    site_name: Optional[str] = None
    charger_id: Optional[str] = None
    inspection_cycle: str
    inspection_type: str
    checklist: List[ChecklistItem]
    memo_text: str = ""
    photo_urls: List[str] = []
    ai_summary: Optional[Any] = None

@router.get("/inspection/preset", response_model=PresetResponse)
def get_preset_checklist(target: str = "충전기", cycle: str = "월간"):
    presets = svc.preset_checklist(target, cycle)
    checklist = [ChecklistItem(item=x.get("item", ""), status=x.get("status", "정상"), note=x.get("note", "")) for x in presets]
    return PresetResponse(checklist=checklist)

@router.post("/inspection/draft", response_model=DraftResponse)
def create_ai_draft(req: DraftRequest, db: Session = Depends(get_db)):
    from services.billing_metering import (
        FEATURE_AI_GENERATION,
        check_quota,
        record_usage,
    )

    tenant_id = (req.tenant_id or "default_tenant").strip()
    check_quota(tenant_id, FEATURE_AI_GENERATION)
    ai_config = resolve_ai_config_for_request(db, tenant_id, req.ai_config)

    # Convert ChecklistItem list to list of dict
    checklist_dict = [x.model_dump() for x in req.checklist]

    # SQLite Lock 방지: LLM 호출 등 장시간 지연 전 읽기 트랜잭션 종료
    db.rollback()

    # 1. RAG 쿼리 추출 (주의/이상 항목 및 메모)
    rag_query_parts = []
    if req.memo:
        rag_query_parts.append(req.memo.strip())
    for item in req.checklist:
        if item.status in ("주의", "이상"):
            rag_query_parts.append(f"{item.item} {item.note}".strip())
    
    similar_cases = None
    if rag_query_parts:
        query_str = " ".join(rag_query_parts)
        similar_cases = _retrieve_similar_cases(query_str)

    try:
        draft_obj, used_model, _web_res, ai_usage = svc.generate_inspection_draft(
            site_name=req.site_name,
            charger_id=None,
            manufacturer=None,
            model_name=None,
            inspection_target=req.target,
            inspection_type=req.inspection_type,
            inspection_cycle=req.cycle,
            checklist=checklist_dict,
            memo_text=req.memo,
            similar_cases=similar_cases,
            ai_config=ai_config,
        )
        fallback_provider = ai_usage.fallback_provider if ai_usage else None
        if not fallback_provider and "->" in used_model:
            fallback_provider = used_model.split("->", 1)[0].split(":")[0]
            
        try:
            record_usage(
                tenant_id,
                FEATURE_AI_GENERATION,
                model_name=used_model or "gpt-4o-mini",
                input_tokens=ai_usage.input_tokens if ai_usage else 0,
                output_tokens=ai_usage.output_tokens if ai_usage else 0,
                fallback_provider=fallback_provider,
                shortcut=(used_model == "faq-shortcut"),
            )
        except Exception as usage_exc:
            print(f"Usage metering failed (draft still returned): {usage_exc}")

        summary_json = draft_obj.model_dump()
        task_type = _resolve_inspection_task_type(req.checklist, req.cycle)
        ai_meta = _build_ai_execution_meta(
            used_model, ai_config, task_type=task_type, usage=ai_usage
        )
        return DraftResponse(
            draft_text=svc.format_inspection_draft_text(draft_obj),
            summary_json=summary_json,
            ai_meta=ai_meta,
        )
    except HTTPException:
        raise
    except Exception as e:
        err = str(e)
        if "429" in err or "insufficient_quota" in err:
            raise HTTPException(
                status_code=503,
                detail=(
                    "AI 서비스 사용 한도가 초과되었습니다. "
                    f"(사유: {err}) 결제/플랜을 확인하거나 잠시 후 다시 시도해 주세요."
                ),
            ) from e
        raise HTTPException(status_code=500, detail=f"AI draft generation failed: {e}") from e

@router.post("/inspection/log")
def save_inspection_log(req: LogCreateRequest):
    checklist_dict = [x.model_dump() for x in req.checklist]
    tenant_id = (req.tenant_id or "default_tenant").strip()
    try:
        inspection_id = repo.create_inspection_log(
            inspection_id=req.inspection_id,
            tenant_id=tenant_id,
            site_id=req.site_id,
            site_name=req.site_name or req.site_id,
            charger_id=req.charger_id,
            inspection_type=req.inspection_type,
            inspection_cycle=req.inspection_cycle,
            checklist=checklist_dict,
            memo_text=req.memo_text,
            photo_paths=req.photo_urls,
            ai_summary=req.ai_summary,
            status="confirmed",
        )
        return {"status": "success", "inspection_id": inspection_id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to save inspection log: {e}")

@router.get("/inspection/logs")
def get_all_inspection_logs(limit: int = 1000):
    try:
        logs = repo.list_inspection_logs(limit=limit)
        results = []
        for l in logs:
            results.append({
                "inspection_id": l.get("inspection_id"),
                "tenant_id": "default_tenant",
                "site_id": l.get("site_name") or "Unknown Site",
                "site_name": l.get("site_name") or "Unknown Site",
                "charger_id": l.get("charger_id") or "-",
                "charger_model": l.get("model_name") or "",
                "inspection_cycle": l.get("inspection_cycle") or "-",
                "inspection_type": l.get("inspection_type") or "-",
                "checklist_json": l.get("checklist") or [],
                "memo_text": l.get("memo_text") or "",
                "photo_urls_json": l.get("photo_paths") or [],
                "ai_summary": l.get("ai_summary"),
                "status": l.get("status") or "draft",
                "created_at": l.get("created_at")
            })
        return results
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to query inspection logs: {e}")

@router.post("/inspection/logs/{inspection_id}/confirm")
def confirm_log(inspection_id: str):
    try:
        repo.confirm_inspection_log(inspection_id=inspection_id)
        return {"status": "confirmed", "inspection_id": inspection_id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to confirm inspection log: {e}")
