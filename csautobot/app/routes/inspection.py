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
from services.ai_provider import AiProviderConfigPayload
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

class DraftResponse(BaseModel):
    draft_text: str
    summary_json: Any

class LogCreateRequest(BaseModel):
    inspection_id: str
    tenant_id: str = "default_tenant"
    site_id: str
    charger_id: Optional[str] = None
    inspection_cycle: str
    inspection_type: str
    checklist: List[ChecklistItem]
    memo_text: str = ""
    photo_urls: List[str] = []
    ai_summary: Optional[str] = None

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
    try:
        draft_obj, used_model, _web_res = svc.generate_inspection_draft(
            site_name=req.site_name,
            charger_id=None,
            manufacturer=None,
            model_name=None,
            inspection_target=req.target,
            inspection_type=req.inspection_type,
            inspection_cycle=req.cycle,
            checklist=checklist_dict,
            memo_text=req.memo,
            ai_config=ai_config,
        )
        record_usage(tenant_id, FEATURE_AI_GENERATION, model_name=used_model or "gpt-4o-mini")
        summary_json = draft_obj.model_dump()
        return DraftResponse(
            draft_text=svc.format_inspection_draft_text(draft_obj),
            summary_json=summary_json,
        )
    except HTTPException:
        raise
    except Exception as e:
        err = str(e)
        if "429" in err or "insufficient_quota" in err:
            raise HTTPException(
                status_code=503,
                detail=(
                    "OpenAI API 사용 한도가 초과되었습니다. "
                    "결제/플랜을 확인하거나 잠시 후 다시 시도해 주세요."
                ),
            ) from e
        raise HTTPException(status_code=500, detail=f"AI draft generation failed: {e}") from e

@router.post("/inspection/log")
def save_inspection_log(req: LogCreateRequest):
    checklist_dict = [x.model_dump() for x in req.checklist]
    try:
        inspection_id = repo.create_inspection_log(
            inspection_id=req.inspection_id,
            site_name=req.site_id,
            charger_id=req.charger_id,
            inspection_type=req.inspection_type,
            inspection_cycle=req.inspection_cycle,
            checklist=checklist_dict,
            memo_text=req.memo_text,
            photo_paths=req.photo_urls,
            ai_summary=req.ai_summary,
            status="confirmed"
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
